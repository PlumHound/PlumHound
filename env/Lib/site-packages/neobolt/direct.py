#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2019 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
This module contains the low-level functionality required for speaking
Bolt. It is not intended to be used directly by driver users. Instead,
the `session` module provides the main user-facing abstractions.
"""

from __future__ import division


__all__ = [
    "DEFAULT_PORT",
    "AbstractConnectionPool",
    "Connection",
    "ConnectionPool",
    "ServerInfo",
    "connect",
]


from collections import deque
from logging import getLogger
from select import select
from socket import socket, SOL_SOCKET, SO_KEEPALIVE, SHUT_RDWR, error as SocketError, timeout as SocketTimeout, AF_INET, AF_INET6
from struct import pack as struct_pack, unpack as struct_unpack
from threading import RLock, Condition
from sys import platform, version_info

from neobolt.addressing import SocketAddress, Resolver
from neobolt.compat import perf_counter
from neobolt.compat.ssl import SSL_AVAILABLE, HAS_SNI, SSLSocket, SSLError
from neobolt.exceptions import ClientError, ProtocolError, SecurityError, \
    ServiceUnavailable, AuthError, CypherError, IncompleteCommitError
from neobolt.meta import version, import_best
from neobolt.packstream import Packer, Unpacker
from neobolt.security import AuthToken, TRUST_DEFAULT, TRUST_ON_FIRST_USE, KNOWN_HOSTS, PersonalCertificateStore, \
    SecurityPlan

ChunkedInputBuffer = import_best("neobolt.bolt._io", "neobolt.bolt.io").ChunkedInputBuffer
ChunkedOutputBuffer = import_best("neobolt.bolt._io", "neobolt.bolt.io").ChunkedOutputBuffer


DEFAULT_PORT = 7687
MAGIC_PREAMBLE = 0x6060B017

# Connection Pool Management
INFINITE = -1
DEFAULT_MAX_CONNECTION_LIFETIME = 3600  # 1h
DEFAULT_MAX_CONNECTION_POOL_SIZE = 100
DEFAULT_CONNECTION_TIMEOUT = 5.0  # 5s

DEFAULT_KEEP_ALIVE = True

# Connection Settings
DEFAULT_CONNECTION_ACQUISITION_TIMEOUT = 60  # 1m

# Client name
DEFAULT_USER_AGENT = "neobolt/{} Python/{}.{}.{}-{}-{} ({})".format(
    *((version,) + tuple(version_info) + (platform,)))


# Set up logger
log = getLogger("neobolt")
log_debug = log.debug


class ServerInfo(object):

    address = None

    def __init__(self, address, protocol_version):
        self.address = address
        self.protocol_version = protocol_version
        self.metadata = {}

    @property
    def agent(self):
        return self.metadata.get("server")

    @property
    def version(self):
        # TODO 2.0: remove
        return self.agent

    def version_info(self):
        if not self.agent:
            return None
        _, _, value = self.agent.partition("/")
        value = value.replace("-", ".").split(".")
        for i, v in enumerate(value):
            try:
                value[i] = int(v)
            except ValueError:
                pass
        return tuple(value)

    def supports(self, feature):
        if not self.agent:
            return None
        if not self.agent.startswith("Neo4j/"):
            return None
        if feature == "bytes":
            return self.version_info() >= (3, 2)
        elif feature == "run_metadata":
            return self.protocol_version >= 3
        else:
            return None


class ConnectionErrorHandler(object):
    """ A handler for send and receive errors.
    """

    def __init__(self, handlers_by_error_class=None):
        if handlers_by_error_class is None:
            handlers_by_error_class = {}

        self.handlers_by_error_class = handlers_by_error_class
        self.known_errors = tuple(handlers_by_error_class.keys())

    def handle(self, error, unresolved_address):
        try:
            error_class = error.__class__
            handler = self.handlers_by_error_class[error_class]
            handler(unresolved_address)
        except KeyError:
            pass


class Connection(object):
    """ Server connection for Bolt protocol v1.

    A :class:`.Connection` should be constructed following a
    successful Bolt handshake and takes the socket over which
    the handshake was carried out.

    .. note:: logs at INFO level
    """

    #: The protocol version in use on this connection
    protocol_version = 0

    #: Server details for this connection
    server = None

    in_use = False

    _closed = False

    _defunct = False

    #: The pool of which this connection is a member
    pool = None

    #: Error class used for raising connection errors
    Error = ServiceUnavailable

    def __init__(self, protocol_version, unresolved_address, sock, **config):
        self.protocol_version = protocol_version
        self.unresolved_address = unresolved_address
        self.socket = sock
        self.error_handler = config.get("error_handler", ConnectionErrorHandler())
        self.server = ServerInfo(SocketAddress.from_socket(sock), protocol_version)
        self.input_buffer = ChunkedInputBuffer()
        self.output_buffer = ChunkedOutputBuffer()
        self.packer = Packer(self.output_buffer)
        self.unpacker = Unpacker()
        self.responses = deque()
        self._max_connection_lifetime = config.get("max_connection_lifetime", DEFAULT_MAX_CONNECTION_LIFETIME)
        self._creation_timestamp = perf_counter()

        # Determine the user agent and ensure it is a Unicode value
        user_agent = config.get("user_agent", DEFAULT_USER_AGENT)
        if isinstance(user_agent, bytes):
            user_agent = user_agent.decode("UTF-8")
        self.user_agent = user_agent

        # Determine auth details
        auth = config.get("auth")
        if not auth:
            self.auth_dict = {}
        elif isinstance(auth, tuple) and 2 <= len(auth) <= 3:
            self.auth_dict = vars(AuthToken("basic", *auth))
        else:
            try:
                self.auth_dict = vars(auth)
            except (KeyError, TypeError):
                raise AuthError("Cannot determine auth details from %r" % auth)

        # Check for missing password
        try:
            credentials = self.auth_dict["credentials"]
        except KeyError:
            pass
        else:
            if credentials is None:
                raise AuthError("Password cannot be None")

        # Pick up the server certificate, if any
        self.der_encoded_server_certificate = config.get("der_encoded_server_certificate")

    @property
    def secure(self):
        return SSL_AVAILABLE and isinstance(self.socket, SSLSocket)

    @property
    def local_port(self):
        try:
            return self.socket.getsockname()[1]
        except IOError:
            return 0

    def init(self):
        log_debug("[#%04X]  C: INIT %r {...}", self.local_port, self.user_agent)
        self._append(b"\x01", (self.user_agent, self.auth_dict),
                     response=InitResponse(self, on_success=self.server.metadata.update))
        self.sync()
        self.packer.supports_bytes = self.server.supports("bytes")

    def hello(self):
        headers = {"user_agent": self.user_agent}
        headers.update(self.auth_dict)
        logged_headers = dict(headers)
        if "credentials" in logged_headers:
            logged_headers["credentials"] = "*******"
        log_debug("[#%04X]  C: HELLO %r", self.local_port, logged_headers)
        self._append(b"\x01", (headers,),
                     response=InitResponse(self, on_success=self.server.metadata.update))
        self.sync()
        self.packer.supports_bytes = self.server.supports("bytes")

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def run(self, statement, parameters=None, mode=None, bookmarks=None, metadata=None, timeout=None, **handlers):
        if not parameters:
            parameters = {}
        if self.protocol_version >= 3:
            extra = {}
            if mode:
                extra["mode"] = mode
            if bookmarks:
                try:
                    extra["bookmarks"] = list(bookmarks)
                except TypeError:
                    raise TypeError("Bookmarks must be provided within an iterable")
            if metadata:
                try:
                    extra["tx_metadata"] = dict(metadata)
                except TypeError:
                    raise TypeError("Metadata must be coercible to a dict")
            if timeout:
                try:
                    extra["tx_timeout"] = int(1000 * timeout)
                except TypeError:
                    raise TypeError("Timeout must be specified as a number of seconds")
            fields = (statement, parameters, extra)
        else:
            if metadata:
                raise NotImplementedError("Transaction metadata is not supported in Bolt v%d" % self.protocol_version)
            if timeout:
                raise NotImplementedError("Transaction timeouts are not supported in Bolt v%d" % self.protocol_version)
            fields = (statement, parameters)
        log_debug("[#%04X]  C: RUN %s", self.local_port, " ".join(map(repr, fields)))
        if statement.upper() == u"COMMIT":
            self._append(b"\x10", fields, CommitResponse(self, **handlers))
        else:
            self._append(b"\x10", fields, Response(self, **handlers))

    def discard_all(self, **handlers):
        log_debug("[#%04X]  C: DISCARD_ALL", self.local_port)
        self._append(b"\x2F", (), Response(self, **handlers))

    def pull_all(self, **handlers):
        log_debug("[#%04X]  C: PULL_ALL", self.local_port)
        self._append(b"\x3F", (), Response(self, **handlers))

    def begin(self, mode=None, bookmarks=None, metadata=None, timeout=None, **handlers):
        if self.protocol_version >= 3:
            extra = {}
            if mode:
                extra["mode"] = mode
            if bookmarks:
                try:
                    extra["bookmarks"] = list(bookmarks)
                except TypeError:
                    raise TypeError("Bookmarks must be provided within an iterable")
            if metadata:
                try:
                    extra["tx_metadata"] = dict(metadata)
                except TypeError:
                    raise TypeError("Metadata must be coercible to a dict")
            if timeout:
                try:
                    extra["tx_timeout"] = int(1000 * timeout)
                except TypeError:
                    raise TypeError("Timeout must be specified as a number of seconds")
            log_debug("[#%04X]  C: BEGIN %r", self.local_port, extra)
            self._append(b"\x11", (extra,), Response(self, **handlers))
        else:
            extra = {}
            if bookmarks:
                if self.protocol_version < 2:
                    # TODO 2.0: remove
                    extra["bookmark"] = last_bookmark(bookmarks)
                try:
                    extra["bookmarks"] = list(bookmarks)
                except TypeError:
                    raise TypeError("Bookmarks must be provided within an iterable")
            if metadata:
                raise NotImplementedError("Transaction metadata is not supported in Bolt v%d" % self.protocol_version)
            if timeout:
                raise NotImplementedError("Transaction timeouts are not supported in Bolt v%d" % self.protocol_version)
            self.run(u"BEGIN", extra, **handlers)
            self.discard_all(**handlers)

    def commit(self, **handlers):
        if self.protocol_version >= 3:
            log_debug("[#%04X]  C: COMMIT", self.local_port)
            self._append(b"\x12", (), CommitResponse(self, **handlers))
        else:
            self.run(u"COMMIT", {}, **handlers)
            self.discard_all(**handlers)

    def rollback(self, **handlers):
        if self.protocol_version >= 3:
            log_debug("[#%04X]  C: ROLLBACK", self.local_port)
            self._append(b"\x13", (), Response(self, **handlers))
        else:
            self.run(u"ROLLBACK", {}, **handlers)
            self.discard_all(**handlers)

    def _append(self, signature, fields=(), response=None):
        """ Add a message to the outgoing queue.

        :arg signature: the signature of the message
        :arg fields: the fields of the message as a tuple
        :arg response: a response object to handle callbacks
        """
        self.packer.pack_struct(signature, fields)
        self.output_buffer.chunk()
        self.output_buffer.chunk()
        self.responses.append(response)

    def reset(self):
        """ Add a RESET message to the outgoing queue, send
        it and consume all remaining messages.
        """

        def fail(metadata):
            raise ProtocolError("RESET failed %r" % metadata)

        log_debug("[#%04X]  C: RESET", self.local_port)
        self._append(b"\x0F", response=Response(self, on_failure=fail))
        self.sync()

    def send(self):
        try:
            self._send()
        except self.error_handler.known_errors as error:
            self.error_handler.handle(error, self.unresolved_address)
            raise error

    def _send(self):
        """ Send all queued messages to the server.
        """
        data = self.output_buffer.view()
        if not data:
            return
        if self.closed():
            raise self.Error("Failed to write to closed connection "
                             "{!r} ({!r})".format(self.unresolved_address,
                                                  self.server.address))
        if self.defunct():
            raise self.Error("Failed to write to defunct connection "
                             "{!r} ({!r})".format(self.unresolved_address,
                                                  self.server.address))
        try:
            self.socket.sendall(data)
        except SocketError as error:
            if self.pool:
                self.pool.deactivate(self.unresolved_address)
            raise self.Error("Failed to write to defunct connection "
                             "{!r} ({!r})".format(self.unresolved_address,
                                                  self.server.address))
        self.output_buffer.clear()

    def fetch(self):
        try:
            return self._fetch()
        except self.error_handler.known_errors as error:
            self.error_handler.handle(error, self.unresolved_address)
            raise error

    def _fetch(self):
        """ Receive at least one message from the server, if available.

        :return: 2-tuple of number of detail messages and number of summary messages fetched
        """
        if self.closed():
            raise self.Error("Failed to read from closed connection "
                             "{!r} ({!r})".format(self.unresolved_address,
                                                  self.server.address))
        if self.defunct():
            raise self.Error("Failed to read from defunct connection "
                             "{!r} ({!r})".format(self.unresolved_address,
                                                  self.server.address))
        if not self.responses:
            return 0, 0

        self._receive()

        details, summary_signature, summary_metadata = self._unpack()

        if details:
            log_debug("[#%04X]  S: RECORD * %d", self.local_port, len(details))  # TODO
            self.responses[0].on_records(details)

        if summary_signature is None:
            return len(details), 0

        response = self.responses.popleft()
        response.complete = True
        if summary_signature == b"\x70":
            log_debug("[#%04X]  S: SUCCESS %r", self.local_port, summary_metadata)
            response.on_success(summary_metadata or {})
        elif summary_signature == b"\x7E":
            log_debug("[#%04X]  S: IGNORED", self.local_port)
            response.on_ignored(summary_metadata or {})
        elif summary_signature == b"\x7F":
            log_debug("[#%04X]  S: FAILURE %r", self.local_port, summary_metadata)
            response.on_failure(summary_metadata or {})
        else:
            raise ProtocolError("Unexpected response message with signature %02X" % summary_signature)

        return len(details), 1

    def _receive(self):
        received = self.input_buffer.receive_message(self.socket, 8192)
        if received == 0:
            message = ("Failed to read from defunct connection "
                       "{!r} ({!r})".format(self.unresolved_address,
                                            self.server.address))
            # We were attempting to receive data but the connection
            # has unexpectedly terminated. So, we need to close the
            # connection from the client side, and remove the address
            # from the connection pool.
            self._defunct = True
            self.close()
            if self.pool:
                self.pool.deactivate(self.unresolved_address)
            # Iterate through the outstanding responses, and if any correspond
            # to COMMIT requests then raise an error to signal that we are
            # unable to confirm that the COMMIT completed successfully.
            for response in self.responses:
                if isinstance(response, CommitResponse):
                    raise IncompleteCommitError(message)
            raise self.Error(message)
        elif received == -1:
            raise KeyboardInterrupt()

    def _unpack(self):
        unpacker = self.unpacker
        input_buffer = self.input_buffer

        details = []
        summary_signature = None
        summary_metadata = None
        more = True
        while more:
            unpacker.attach(input_buffer.frame())
            size, signature = unpacker.unpack_structure_header()
            if size > 1:
                raise ProtocolError("Expected one field")
            if signature == b"\x71":
                data = unpacker.unpack_list()
                details.append(data)
                more = input_buffer.frame_message()
            else:
                summary_signature = signature
                summary_metadata = unpacker.unpack_map()
                more = False
        return details, summary_signature, summary_metadata

    def timedout(self):
        return 0 <= self._max_connection_lifetime <= perf_counter() - self._creation_timestamp

    def sync(self):
        """ Send and fetch all outstanding messages.

        :return: 2-tuple of number of detail messages and number of summary messages fetched
        """
        self.send()
        detail_count = summary_count = 0
        while self.responses:
            response = self.responses[0]
            while not response.complete:
                detail_delta, summary_delta = self.fetch()
                detail_count += detail_delta
                summary_count += summary_delta
        return detail_count, summary_count

    def close(self):
        """ Close the connection.
        """
        if not self._closed:
            if not self._defunct and self.protocol_version >= 3:
                log_debug("[#%04X]  C: GOODBYE", self.local_port)
                self._append(b"\x02", ())
                try:
                    self.send()
                except ServiceUnavailable:
                    pass
            log_debug("[#%04X]  C: <CLOSE>", self.local_port)
            try:
                self.socket.close()
            except IOError:
                pass
            finally:
                self._closed = True

    def closed(self):
        return self._closed

    def defunct(self):
        return self._defunct


class AbstractConnectionPool(object):
    """ A collection of connections to one or more server addresses.
    """

    _closed = False

    def __init__(self, connector, connection_error_handler, **config):
        self.connector = connector
        self.connection_error_handler = connection_error_handler
        self.connections = {}
        self.lock = RLock()
        self.cond = Condition(self.lock)
        self._max_connection_pool_size = config.get("max_connection_pool_size", DEFAULT_MAX_CONNECTION_POOL_SIZE)
        self._connection_acquisition_timeout = config.get("connection_acquisition_timeout", DEFAULT_CONNECTION_ACQUISITION_TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def acquire_direct(self, address):
        """ Acquire a connection to a given address from the pool.
        The address supplied should always be an IP address, not
        a host name.

        This method is thread safe.
        """
        if self.closed():
            raise ServiceUnavailable("Connection pool closed")
        with self.lock:
            try:
                connections = self.connections[address]
            except KeyError:
                connections = self.connections[address] = deque()

            connection_acquisition_start_timestamp = perf_counter()
            while True:
                # try to find a free connection in pool
                for connection in list(connections):
                    if connection.closed() or connection.defunct() or connection.timedout():
                        connections.remove(connection)
                        continue
                    if not connection.in_use:
                        connection.in_use = True
                        return connection
                # all connections in pool are in-use
                can_create_new_connection = self._max_connection_pool_size == INFINITE or len(connections) < self._max_connection_pool_size
                if can_create_new_connection:
                    try:
                        connection = self.connector(address, error_handler=self.connection_error_handler)
                    except ServiceUnavailable:
                        self.remove(address)
                        raise
                    else:
                        connection.pool = self
                        connection.in_use = True
                        connections.append(connection)
                        return connection

                # failed to obtain a connection from pool because the pool is full and no free connection in the pool
                span_timeout = self._connection_acquisition_timeout - (perf_counter() - connection_acquisition_start_timestamp)
                if span_timeout > 0:
                    self.cond.wait(span_timeout)
                    # if timed out, then we throw error. This time computation is needed, as with python 2.7, we cannot
                    # tell if the condition is notified or timed out when we come to this line
                    if self._connection_acquisition_timeout <= (perf_counter() - connection_acquisition_start_timestamp):
                        raise ClientError("Failed to obtain a connection from pool within {!r}s".format(
                            self._connection_acquisition_timeout))
                else:
                    raise ClientError("Failed to obtain a connection from pool within {!r}s".format(self._connection_acquisition_timeout))

    def acquire(self, access_mode=None):
        """ Acquire a connection to a server that can satisfy a set of parameters.

        :param access_mode:
        """

    def release(self, connection):
        """ Release a connection back into the pool.
        This method is thread safe.
        """
        with self.lock:
            connection.in_use = False
            self.cond.notify_all()

    def in_use_connection_count(self, address):
        """ Count the number of connections currently in use to a given
        address.
        """
        try:
            connections = self.connections[address]
        except KeyError:
            return 0
        else:
            return sum(1 if connection.in_use else 0 for connection in connections)

    def deactivate(self, address):
        """ Deactivate an address from the connection pool, if present, closing
        all idle connection to that address
        """
        with self.lock:
            try:
                connections = self.connections[address]
            except KeyError: # already removed from the connection pool
                return
            for conn in list(connections):
                if not conn.in_use:
                    connections.remove(conn)
                    try:
                        conn.close()
                    except IOError:
                        pass
            if not connections:
                self.remove(address)

    def remove(self, address):
        """ Remove an address from the connection pool, if present, closing
        all connections to that address.
        """
        with self.lock:
            for connection in self.connections.pop(address, ()):
                try:
                    connection.close()
                except IOError:
                    pass

    def close(self):
        """ Close all connections and empty the pool.
        This method is thread safe.
        """
        if self._closed:
            return
        try:
            with self.lock:
                if not self._closed:
                    self._closed = True
                    for address in list(self.connections):
                        self.remove(address)
        except TypeError as e:
            pass

    def closed(self):
        """ Return :const:`True` if this pool is closed, :const:`False`
        otherwise.
        """
        with self.lock:
            return self._closed


class ConnectionPool(AbstractConnectionPool):

    def __init__(self, connector, address, **config):
        super(ConnectionPool, self).__init__(connector, ConnectionErrorHandler(), **config)
        self.address = address

    def acquire(self, access_mode=None):
        return self.acquire_direct(self.address)


class Response(object):
    """ Subscriber object for a full response (zero or
    more detail messages followed by one summary message).
    """

    def __init__(self, connection, **handlers):
        self.connection = connection
        self.handlers = handlers
        self.complete = False

    def on_records(self, records):
        """ Called when one or more RECORD messages have been received.
        """
        handler = self.handlers.get("on_records")
        if callable(handler):
            handler(records)

    def on_success(self, metadata):
        """ Called when a SUCCESS message has been received.
        """
        handler = self.handlers.get("on_success")
        if callable(handler):
            handler(metadata)
        handler = self.handlers.get("on_summary")
        if callable(handler):
            handler()

    def on_failure(self, metadata):
        """ Called when a FAILURE message has been received.
        """
        self.connection.reset()
        handler = self.handlers.get("on_failure")
        if callable(handler):
            handler(metadata)
        handler = self.handlers.get("on_summary")
        if callable(handler):
            handler()
        raise CypherError.hydrate(**metadata)

    def on_ignored(self, metadata=None):
        """ Called when an IGNORED message has been received.
        """
        handler = self.handlers.get("on_ignored")
        if callable(handler):
            handler(metadata)
        handler = self.handlers.get("on_summary")
        if callable(handler):
            handler()


class InitResponse(Response):

    def on_failure(self, metadata):
        code = metadata.get("code")
        message = metadata.get("message", "Connection initialisation failed")
        if code == "Neo.ClientError.Security.Unauthorized":
            raise AuthError(message)
        else:
            raise ServiceUnavailable(message)


class CommitResponse(Response):

    pass


# TODO: remove in 2.0
def _last_bookmark(b0, b1):
    """ Return the latest of two bookmarks by looking for the maximum
    integer value following the last colon in the bookmark string.
    """
    n = [None, None]
    _, _, n[0] = b0.rpartition(":")
    _, _, n[1] = b1.rpartition(":")
    for i in range(2):
        try:
            n[i] = int(n[i])
        except ValueError:
            raise ValueError("Invalid bookmark: {}".format(b0))
    return b0 if n[0] > n[1] else b1


# TODO: remove in 2.0
def last_bookmark(bookmarks):
    """ The bookmark returned by the last :class:`.Transaction`.
    """
    last = None
    for bookmark in bookmarks:
        if last is None:
            last = bookmark
        else:
            last = _last_bookmark(last, bookmark)
    return last


def _connect(resolved_address, **config):
    """

    :param resolved_address:
    :param config:
    :return: socket object
    """
    s = None
    try:
        if len(resolved_address) == 2:
            s = socket(AF_INET)
        elif len(resolved_address) == 4:
            s = socket(AF_INET6)
        else:
            raise ValueError("Unsupported address {!r}".format(resolved_address))
        t = s.gettimeout()
        s.settimeout(config.get("connection_timeout", DEFAULT_CONNECTION_TIMEOUT))
        log_debug("[#0000]  C: <OPEN> %s", resolved_address)
        s.connect(resolved_address)
        s.settimeout(t)
        s.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1 if config.get("keep_alive", DEFAULT_KEEP_ALIVE) else 0)
    except SocketTimeout:
        log_debug("[#0000]  C: <TIMEOUT> %s", resolved_address)
        log_debug("[#0000]  C: <CLOSE> %s", resolved_address)
        s.close()
        raise ServiceUnavailable("Timed out trying to establish connection to {!r}".format(resolved_address))
    except (IOError, OSError) as error:  # TODO 2.0: remove IOError alias
        log_debug("[#0000]  C: <ERROR> %s %s", type(error).__name__, " ".join(map(repr, error.args)))
        log_debug("[#0000]  C: <CLOSE> %s", resolved_address)
        s.close()
        raise ServiceUnavailable("Failed to establish connection to {!r} (reason {})".format(resolved_address, error))
    else:
        return s


def _secure(s, host, ssl_context, **config):
    local_port = s.getsockname()[1]
    # Secure the connection if an SSL context has been provided
    if ssl_context and SSL_AVAILABLE:
        log_debug("[#%04X]  C: <SECURE> %s", local_port, host)
        try:
            s = ssl_context.wrap_socket(s, server_hostname=host if HAS_SNI and host else None)
        except SSLError as cause:
            s.close()
            error = SecurityError("Failed to establish secure connection to {!r}".format(cause.args[1]))
            error.__cause__ = cause
            raise error
        else:
            # Check that the server provides a certificate
            der_encoded_server_certificate = s.getpeercert(binary_form=True)
            if der_encoded_server_certificate is None:
                s.close()
                raise ProtocolError("When using a secure socket, the server should always "
                                    "provide a certificate")
            trust = config.get("trust", TRUST_DEFAULT)
            if trust == TRUST_ON_FIRST_USE:
                store = PersonalCertificateStore()
                if not store.match_or_trust(host, der_encoded_server_certificate):
                    s.close()
                    raise ProtocolError("Server certificate does not match known certificate "
                                        "for %r; check details in file %r" % (host, KNOWN_HOSTS))
    else:
        der_encoded_server_certificate = None
    return s, der_encoded_server_certificate


def _handshake(s, resolved_address, der_encoded_server_certificate, **config):
    """

    :param s:
    :return:
    """
    local_port = s.getsockname()[1]

    # Send details of the protocol versions supported
    supported_versions = [3, 2, 1, 0]
    handshake = [MAGIC_PREAMBLE] + supported_versions
    log_debug("[#%04X]  C: <MAGIC> 0x%08X", local_port, MAGIC_PREAMBLE)
    log_debug("[#%04X]  C: <HANDSHAKE> 0x%08X 0x%08X 0x%08X 0x%08X", local_port, *supported_versions)
    data = b"".join(struct_pack(">I", num) for num in handshake)
    s.sendall(data)

    # Handle the handshake response
    ready_to_read = False
    while not ready_to_read:
        ready_to_read, _, _ = select((s,), (), (), 1)
    try:
        data = s.recv(4)
    except (IOError, OSError):  # TODO 2.0: remove IOError alias
        raise ServiceUnavailable("Failed to read any data from server {!r} after connected".format(resolved_address))
    data_size = len(data)
    if data_size == 0:
        # If no data is returned after a successful select
        # response, the server has closed the connection
        log_debug("[#%04X]  S: <CLOSE>", local_port)
        s.close()
        raise ServiceUnavailable("Connection to %r closed without handshake response" % (resolved_address,))
    if data_size != 4:
        # Some garbled data has been received
        log_debug("[#%04X]  S: @*#!", local_port)
        s.close()
        raise ProtocolError("Expected four byte Bolt handshake response from %r, received %r instead; "
                            "check for incorrect port number" % (resolved_address, data))
    agreed_version, = struct_unpack(">I", data)
    log_debug("[#%04X]  S: <HANDSHAKE> 0x%08X", local_port, agreed_version)
    if agreed_version == 0:
        log_debug("[#%04X]  C: <CLOSE>", local_port)
        s.shutdown(SHUT_RDWR)
        s.close()
    elif agreed_version in (1, 2):
        connection = Connection(agreed_version, resolved_address, s,
                                der_encoded_server_certificate=der_encoded_server_certificate,
                                **config)
        connection.init()
        return connection
    elif agreed_version in (3,):
        connection = Connection(agreed_version, resolved_address, s,
                                der_encoded_server_certificate=der_encoded_server_certificate,
                                **config)
        connection.hello()
        return connection
    elif agreed_version == 0x48545450:
        log_debug("[#%04X]  S: <CLOSE>", local_port)
        s.close()
        raise ServiceUnavailable("Cannot to connect to Bolt service on {!r} "
                                 "(looks like HTTP)".format(resolved_address))
    else:
        log_debug("[#%04X]  S: <CLOSE>", local_port)
        s.close()
        raise ProtocolError("Unknown Bolt protocol version: {}".format(agreed_version))


def connect(address, **config):
    """ Connect and perform a handshake and return a valid Connection object, assuming
    a protocol version can be agreed.
    """
    security_plan = SecurityPlan.build(**config)
    last_error = None
    # Establish a connection to the host and port specified
    # Catches refused connections see:
    # https://docs.python.org/2/library/errno.html
    log_debug("[#0000]  C: <RESOLVE> %s", address)
    resolver = Resolver(custom_resolver=config.get("resolver"))
    resolver.addresses.append(address)
    resolver.custom_resolve()
    resolver.dns_resolve()
    for resolved_address in resolver.addresses:
        try:
            host = address[0]
            s = _connect(resolved_address, **config)
            s, der_encoded_server_certificate = _secure(s, host, security_plan.ssl_context, **config)
            connection = _handshake(s, address, der_encoded_server_certificate, **config)
        except Exception as error:
            last_error = error
        else:
            return connection
    if last_error is None:
        raise ServiceUnavailable("Failed to resolve addresses for %s" % address)
    else:
        raise last_error
