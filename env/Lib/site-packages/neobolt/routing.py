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


from abc import abstractmethod
from logging import getLogger
from sys import maxsize
from threading import Lock

from neobolt.addressing import SocketAddress
from neobolt.compat import perf_counter
from neobolt.compat.collections import MutableSet, OrderedDict
from neobolt.direct import AbstractConnectionPool, DEFAULT_PORT, ConnectionErrorHandler
from neobolt.exceptions import ConnectionExpired, DatabaseUnavailableError, \
    NotALeaderError, ForbiddenOnReadOnlyDatabaseError, ServiceUnavailable
from neobolt.versioning import Version


READ_ACCESS = "READ"
WRITE_ACCESS = "WRITE"

INITIAL_RETRY_DELAY = 1.0
RETRY_DELAY_MULTIPLIER = 2.0
RETRY_DELAY_JITTER_FACTOR = 0.2

DEFAULT_MAX_RETRY_TIME = 30.0  # seconds

LOAD_BALANCING_STRATEGY_LEAST_CONNECTED = 0
LOAD_BALANCING_STRATEGY_ROUND_ROBIN = 1
DEFAULT_LOAD_BALANCING_STRATEGY = LOAD_BALANCING_STRATEGY_LEAST_CONNECTED


log = getLogger("neobolt")


class OrderedSet(MutableSet):

    def __init__(self, elements=()):
        self._elements = OrderedDict.fromkeys(elements)
        self._current = None

    def __repr__(self):
        return "{%s}" % ", ".join(map(repr, self._elements))

    def __contains__(self, element):
        return element in self._elements

    def __iter__(self):
        return iter(self._elements)

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, index):
        return list(self._elements.keys())[index]

    def add(self, element):
        self._elements[element] = None

    def clear(self):
        self._elements.clear()

    def discard(self, element):
        try:
            del self._elements[element]
        except KeyError:
            pass

    def remove(self, element):
        try:
            del self._elements[element]
        except KeyError:
            raise ValueError(element)

    def update(self, elements=()):
        self._elements.update(OrderedDict.fromkeys(elements))

    def replace(self, elements=()):
        e = self._elements
        e.clear()
        e.update(OrderedDict.fromkeys(elements))


class RoutingTable(object):

    @classmethod
    def parse_routing_info(cls, records):
        """ Parse the records returned from a getServers call and
        return a new RoutingTable instance.
        """
        if len(records) != 1:
            raise RoutingProtocolError("Expected exactly one record")
        record = records[0]
        routers = []
        readers = []
        writers = []
        try:
            servers = record["servers"]
            for server in servers:
                role = server["role"]
                addresses = []
                for address in server["addresses"]:
                    addresses.append(SocketAddress.parse(address, DEFAULT_PORT))
                if role == "ROUTE":
                    routers.extend(addresses)
                elif role == "READ":
                    readers.extend(addresses)
                elif role == "WRITE":
                    writers.extend(addresses)
            ttl = record["ttl"]
        except (KeyError, TypeError):
            raise RoutingProtocolError("Cannot parse routing info")
        else:
            return cls(routers, readers, writers, ttl)

    def __init__(self, routers=(), readers=(), writers=(), ttl=0):
        self.routers = OrderedSet(routers)
        self.readers = OrderedSet(readers)
        self.writers = OrderedSet(writers)
        self.last_updated_time = perf_counter()
        self.ttl = ttl

    def is_fresh(self, access_mode):
        """ Indicator for whether routing information is still usable.
        """
        expired = self.last_updated_time + self.ttl <= perf_counter()
        has_server_for_mode = (access_mode == READ_ACCESS and self.readers) or (access_mode == WRITE_ACCESS and self.writers)
        return not expired and self.routers and has_server_for_mode

    def update(self, new_routing_table):
        """ Update the current routing table with new routing information
        from a replacement table.
        """
        self.routers.replace(new_routing_table.routers)
        self.readers.replace(new_routing_table.readers)
        self.writers.replace(new_routing_table.writers)
        self.last_updated_time = perf_counter()
        self.ttl = new_routing_table.ttl

    def servers(self):
        return set(self.routers) | set(self.writers) | set(self.readers)


class LoadBalancingStrategy(object):

    @classmethod
    def build(cls, connection_pool, **config):
        load_balancing_strategy = config.get("load_balancing_strategy", DEFAULT_LOAD_BALANCING_STRATEGY)
        if load_balancing_strategy == LOAD_BALANCING_STRATEGY_LEAST_CONNECTED:
            return LeastConnectedLoadBalancingStrategy(connection_pool)
        elif load_balancing_strategy == LOAD_BALANCING_STRATEGY_ROUND_ROBIN:
            return RoundRobinLoadBalancingStrategy()
        else:
            raise ValueError("Unknown load balancing strategy '%s'" % load_balancing_strategy)

    @abstractmethod
    def select_reader(self, known_readers):
        raise NotImplementedError()

    @abstractmethod
    def select_writer(self, known_writers):
        raise NotImplementedError()


class RoundRobinLoadBalancingStrategy(LoadBalancingStrategy):

    _readers_offset = 0
    _writers_offset = 0

    def select_reader(self, known_readers):
        address = self._select(self._readers_offset, known_readers)
        self._readers_offset += 1
        return address

    def select_writer(self, known_writers):
        address = self._select(self._writers_offset, known_writers)
        self._writers_offset += 1
        return address

    @classmethod
    def _select(cls, offset, addresses):
        if not addresses:
            return None
        return addresses[offset % len(addresses)]


class LeastConnectedLoadBalancingStrategy(LoadBalancingStrategy):

    def __init__(self, connection_pool):
        self._readers_offset = 0
        self._writers_offset = 0
        self._connection_pool = connection_pool

    def select_reader(self, known_readers):
        address = self._select(self._readers_offset, known_readers)
        self._readers_offset += 1
        return address

    def select_writer(self, known_writers):
        address = self._select(self._writers_offset, known_writers)
        self._writers_offset += 1
        return address

    def _select(self, offset, addresses):
        if not addresses:
            return None
        num_addresses = len(addresses)
        start_index = offset % num_addresses
        index = start_index

        least_connected_address = None
        least_in_use_connections = maxsize

        while True:
            address = addresses[index]
            index = (index + 1) % num_addresses

            in_use_connections = self._connection_pool.in_use_connection_count(address)

            if in_use_connections < least_in_use_connections:
                least_connected_address = address
                least_in_use_connections = in_use_connections

            if index == start_index:
                return least_connected_address


class RoutingConnectionErrorHandler(ConnectionErrorHandler):
    """ Handler for errors in routing driver connections.
    """

    def __init__(self, pool):
        super(RoutingConnectionErrorHandler, self).__init__({
            ConnectionExpired: lambda address: pool.deactivate(address),
            ServiceUnavailable: lambda address: pool.deactivate(address),
            DatabaseUnavailableError: lambda address: pool.deactivate(address),
            NotALeaderError: lambda address: pool.remove_writer(address),
            ForbiddenOnReadOnlyDatabaseError: lambda address: pool.remove_writer(address)
        })


class RoutingConnectionPool(AbstractConnectionPool):
    """ Connection pool with routing table.
    """

    def __init__(self, connector, initial_address, routing_context, *routers, **config):
        super(RoutingConnectionPool, self).__init__(connector, RoutingConnectionErrorHandler(self), **config)
        self.initial_address = initial_address
        self.routing_context = routing_context
        self.routing_table = RoutingTable(routers)
        self.missing_writer = False
        self.refresh_lock = Lock()
        self.load_balancing_strategy = LoadBalancingStrategy.build(self, **config)

    def fetch_routing_info(self, address):
        """ Fetch raw routing info from a given router address.

        :param address: router address
        :return: list of routing records or
                 None if no connection could be established
        :raise ServiceUnavailable: if the server does not support routing or
                                   if routing support is broken
        """
        metadata = {}
        records = []

        def fail(md):
            if md.get("code") == "Neo.ClientError.Procedure.ProcedureNotFound":
                raise RoutingProtocolError("Server {!r} does not support routing".format(address))
            else:
                raise RoutingProtocolError("Routing support broken on server {!r}".format(address))

        try:
            with self.acquire_direct(address) as cx:
                _, _, server_version = (cx.server.agent or "").partition("/")
                if server_version and Version.parse(server_version) >= Version((3, 2)):
                    cx.run("CALL dbms.cluster.routing.getRoutingTable($context)",
                           {"context": self.routing_context}, on_success=metadata.update, on_failure=fail)
                else:
                    cx.run("CALL dbms.cluster.routing.getServers", {}, on_success=metadata.update, on_failure=fail)
                cx.pull_all(on_success=metadata.update, on_records=records.extend)
                cx.sync()
        except RoutingProtocolError as error:
            raise ServiceUnavailable(*error.args)
        except ServiceUnavailable:
            self.deactivate(address)
            return None
        else:
            return [dict(zip(metadata.get("fields", ()), values)) for values in records]

    def fetch_routing_table(self, address):
        """ Fetch a routing table from a given router address.

        :param address: router address
        :return: a new RoutingTable instance or None if the given router is
                 currently unable to provide routing information
        :raise ServiceUnavailable: if no writers are available
        :raise ProtocolError: if the routing information received is unusable
        """
        new_routing_info = self.fetch_routing_info(address)
        if new_routing_info is None:
            return None

        # Parse routing info and count the number of each type of server
        new_routing_table = RoutingTable.parse_routing_info(new_routing_info)
        num_routers = len(new_routing_table.routers)
        num_readers = len(new_routing_table.readers)
        num_writers = len(new_routing_table.writers)

        # No writers are available. This likely indicates a temporary state,
        # such as leader switching, so we should not signal an error.
        # When no writers available, then we flag we are reading in absence of writer
        self.missing_writer = (num_writers == 0)

        # No routers
        if num_routers == 0:
            raise RoutingProtocolError("No routing servers returned from server %r" % (address,))

        # No readers
        if num_readers == 0:
            raise RoutingProtocolError("No read servers returned from server %r" % (address,))

        # At least one of each is fine, so return this table
        return new_routing_table

    def update_routing_table_from(self, *routers):
        """ Try to update routing tables with the given routers.

        :return: True if the routing table is successfully updated,
        otherwise False
        """
        log.debug("Attempting to update routing table from "
                  "{}".format(", ".join(map(repr, routers))))
        for router in routers:
            new_routing_table = self.fetch_routing_table(router)
            if new_routing_table is not None:
                self.routing_table.update(new_routing_table)
                log.debug("Successfully updated routing table from "
                          "{!r} ({!r})".format(router, self.routing_table))
                return True
        return False

    def update_routing_table(self):
        """ Update the routing table from the first router able to provide
        valid routing information.
        """
        # copied because it can be modified
        existing_routers = list(self.routing_table.routers)

        has_tried_initial_routers = False
        if self.missing_writer:
            has_tried_initial_routers = True
            if self.update_routing_table_from(self.initial_address):
                return

        if self.update_routing_table_from(*existing_routers):
            return

        if not has_tried_initial_routers and self.initial_address not in existing_routers:
            if self.update_routing_table_from(self.initial_address):
                return

        # None of the routers have been successful, so just fail
        log.error("Unable to retrieve routing information")
        raise ServiceUnavailable("Unable to retrieve routing information")

    def update_connection_pool(self):
        servers = self.routing_table.servers()
        for address in list(self.connections):
            if address not in servers:
                super(RoutingConnectionPool, self).deactivate(address)

    def ensure_routing_table_is_fresh(self, access_mode):
        """ Update the routing table if stale.

        This method performs two freshness checks, before and after acquiring
        the refresh lock. If the routing table is already fresh on entry, the
        method exits immediately; otherwise, the refresh lock is acquired and
        the second freshness check that follows determines whether an update
        is still required.

        This method is thread-safe.

        :return: `True` if an update was required, `False` otherwise.
        """
        if self.routing_table.is_fresh(access_mode):
            return False
        with self.refresh_lock:
            if self.routing_table.is_fresh(access_mode):
                if access_mode == READ_ACCESS:
                    # if reader is fresh but writers is not fresh, then we are reading in absence of writer
                    self.missing_writer = not self.routing_table.is_fresh(WRITE_ACCESS)
                return False
            self.update_routing_table()
            self.update_connection_pool()
            return True

    def acquire(self, access_mode=None):
        if access_mode is None:
            access_mode = WRITE_ACCESS
        if access_mode == READ_ACCESS:
            server_list = self.routing_table.readers
            server_selector = self.load_balancing_strategy.select_reader
        elif access_mode == WRITE_ACCESS:
            server_list = self.routing_table.writers
            server_selector = self.load_balancing_strategy.select_writer
        else:
            raise ValueError("Unsupported access mode {}".format(access_mode))

        self.ensure_routing_table_is_fresh(access_mode)
        while True:
            address = server_selector(server_list)
            if address is None:
                break
            try:
                connection = self.acquire_direct(address)  # should always be a resolved address
                connection.Error = ConnectionExpired
            except ServiceUnavailable:
                self.deactivate(address)
            else:
                return connection
        raise ConnectionExpired("Failed to obtain connection towards '%s' server." % access_mode)

    def deactivate(self, address):
        """ Deactivate an address from the connection pool,
        if present, remove from the routing table and also closing
        all idle connections to that address.
        """
        # We use `discard` instead of `remove` here since the former
        # will not fail if the address has already been removed.
        self.routing_table.routers.discard(address)
        self.routing_table.readers.discard(address)
        self.routing_table.writers.discard(address)
        super(RoutingConnectionPool, self).deactivate(address)

    def remove_writer(self, address):
        """ Remove a writer address from the routing table, if present.
        """
        self.routing_table.writers.discard(address)


class RoutingProtocolError(Exception):
    """ Raised when a fault occurs with the routing protocol.
    """
