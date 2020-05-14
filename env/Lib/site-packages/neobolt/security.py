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


from genericpath import isfile
from base64 import b64encode
from os import makedirs, open as os_open, write as os_write, close as os_close, O_CREAT, O_APPEND, O_WRONLY
from os.path import dirname, join as path_join, expanduser
from warnings import warn

from neobolt.compat.ssl import SSL_AVAILABLE, SSLContext, PROTOCOL_SSLv23, OP_NO_SSLv2, CERT_REQUIRED


ENCRYPTION_OFF = 0
ENCRYPTION_ON = 1
ENCRYPTION_DEFAULT = ENCRYPTION_OFF


TRUST_ON_FIRST_USE = 0  # Deprecated
TRUST_SIGNED_CERTIFICATES = 1  # Deprecated
TRUST_ALL_CERTIFICATES = 2
TRUST_CUSTOM_CA_SIGNED_CERTIFICATES = 3
TRUST_SYSTEM_CA_SIGNED_CERTIFICATES = 4
TRUST_DEFAULT = TRUST_ALL_CERTIFICATES


KNOWN_HOSTS = path_join(expanduser("~"), ".neo4j", "known_hosts")


class AuthToken(object):
    """ Container for auth information
    """

    #: By default we should not send any realm
    realm = None

    def __init__(self, scheme, principal, credentials, realm=None, **parameters):
        self.scheme = scheme
        self.principal = principal
        self.credentials = credentials
        if realm:
            self.realm = realm
        if parameters:
            self.parameters = parameters


class SecurityPlan(object):

    @classmethod
    def build(cls, **config):
        encrypted = config.get("encrypted", ENCRYPTION_DEFAULT)
        if encrypted is None and ENCRYPTION_DEFAULT == ENCRYPTION_ON:
            encrypted = _encryption_default()
        trust = config.get("trust", TRUST_DEFAULT)
        if encrypted:
            if not SSL_AVAILABLE:
                raise RuntimeError("Bolt over TLS is only available in Python 2.7.9+ and "
                                   "Python 3.3+")
            ssl_context = SSLContext(PROTOCOL_SSLv23)
            ssl_context.options |= OP_NO_SSLv2
            if trust == TRUST_ON_FIRST_USE:
                warn("TRUST_ON_FIRST_USE is deprecated, please use "
                     "TRUST_ALL_CERTIFICATES instead")
            elif trust == TRUST_SIGNED_CERTIFICATES:
                warn("TRUST_SIGNED_CERTIFICATES is deprecated, please use "
                     "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES instead")
                ssl_context.verify_mode = CERT_REQUIRED
            elif trust == TRUST_ALL_CERTIFICATES:
                pass
            elif trust == TRUST_CUSTOM_CA_SIGNED_CERTIFICATES:
                raise NotImplementedError("Custom CA support is not implemented")
            elif trust == TRUST_SYSTEM_CA_SIGNED_CERTIFICATES:
                ssl_context.verify_mode = CERT_REQUIRED
            else:
                raise ValueError("Unknown trust mode")
            ssl_context.set_default_verify_paths()
        else:
            ssl_context = None
        return cls(encrypted, ssl_context, trust != TRUST_ON_FIRST_USE)

    def __init__(self, requires_encryption, ssl_context, routing_compatible):
        self.encrypted = bool(requires_encryption)
        self.ssl_context = ssl_context
        self.routing_compatible = routing_compatible


_warned_about_insecure_default = False


def _encryption_default():
    global _warned_about_insecure_default
    if not SSL_AVAILABLE and not _warned_about_insecure_default:
        warn("Bolt over TLS is only available in Python 2.7.9+ and Python 3.3+ "
             "so communications are not secure")
        _warned_about_insecure_default = True
    return ENCRYPTION_DEFAULT


class CertificateStore(object):

    def match_or_trust(self, host, der_encoded_certificate):
        """ Check whether the supplied certificate matches that stored for the
        specified host. If it does, return ``True``, if it doesn't, return
        ``False``. If no entry for that host is found, add it to the store
        and return ``True``.

        :arg host:
        :arg der_encoded_certificate:
        :return:
        """
        raise NotImplementedError()


class PersonalCertificateStore(CertificateStore):

    def __init__(self, path=None):
        self.path = path or KNOWN_HOSTS

    def match_or_trust(self, host, der_encoded_certificate):
        base64_encoded_certificate = b64encode(der_encoded_certificate)
        if isfile(self.path):
            with open(self.path) as f_in:
                for line in f_in:
                    known_host, _, known_cert = line.strip().partition(":")
                    known_cert = known_cert.encode("utf-8")
                    if host == known_host:
                        return base64_encoded_certificate == known_cert
        # First use (no hosts match)
        try:
            makedirs(dirname(self.path))
        except OSError:
            pass
        f_out = os_open(self.path, O_CREAT | O_APPEND | O_WRONLY, 0o600)  # TODO: Windows
        if isinstance(host, bytes):
            os_write(f_out, host)
        else:
            os_write(f_out, host.encode("utf-8"))
        os_write(f_out, b":")
        os_write(f_out, base64_encoded_certificate)
        os_write(f_out, b"\n")
        os_close(f_out)
        return True
