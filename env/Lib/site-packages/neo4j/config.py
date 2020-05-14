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


from sys import platform, version_info

from neo4j.meta import version

# Auth
TRUST_ON_FIRST_USE = 0  # Deprecated
TRUST_SIGNED_CERTIFICATES = 1  # Deprecated
TRUST_ALL_CERTIFICATES = 2
TRUST_CUSTOM_CA_SIGNED_CERTIFICATES = 3
TRUST_SYSTEM_CA_SIGNED_CERTIFICATES = 4
TRUST_DEFAULT = TRUST_ALL_CERTIFICATES

# Connection Pool Management
INFINITE = -1
DEFAULT_MAX_CONNECTION_LIFETIME = 3600  # 1h
DEFAULT_MAX_CONNECTION_POOL_SIZE = 100
DEFAULT_CONNECTION_TIMEOUT = 30.0  # 30s

# Connection Settings
DEFAULT_CONNECTION_ACQUISITION_TIMEOUT = 60  # 1m

# Routing settings
DEFAULT_MAX_RETRY_TIME = 30.0  # 30s

LOAD_BALANCING_STRATEGY_LEAST_CONNECTED = 0
LOAD_BALANCING_STRATEGY_ROUND_ROBIN = 1
DEFAULT_LOAD_BALANCING_STRATEGY = LOAD_BALANCING_STRATEGY_LEAST_CONNECTED

# Client name
DEFAULT_USER_AGENT = "neo4j-python/{} Python/{}.{}.{}-{}-{} ({})".format(
    *((version,) + tuple(version_info) + (platform,)))

default_config = {
    "auth": None,  # provide your own authentication token such as {"username", "password"}
    "encrypted": None,  # default to have encryption enabled if ssl is available on your platform
    "trust": TRUST_DEFAULT,
    "der_encoded_server_certificate": None,

    "user_agent": DEFAULT_USER_AGENT,

    # Connection pool management
    "max_connection_lifetime": DEFAULT_MAX_CONNECTION_LIFETIME,
    "max_connection_pool_size": DEFAULT_MAX_CONNECTION_POOL_SIZE,
    "connection_acquisition_timeout": DEFAULT_CONNECTION_ACQUISITION_TIMEOUT,

    # Connection settings:
    "connection_timeout": DEFAULT_CONNECTION_TIMEOUT,
    "keep_alive": True,

    # Routing settings:
    "max_retry_time": DEFAULT_MAX_RETRY_TIME,
    "load_balancing_strategy": DEFAULT_LOAD_BALANCING_STRATEGY,
}
