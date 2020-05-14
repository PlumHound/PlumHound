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
This package contains classes for modelling the standard set of data types
available within a Neo4j graph database. Most non-primitive types are
represented by PackStream structures on the wire before being converted
into concrete values through the PackStreamHydrant.
"""


from neo4j import Record
from neo4j.compat import map_type, string, integer, ustr

# These classes are imported in order to retain backward compatibility with 1.5.
# They should be removed in 2.0.
from .graph import Entity, Node, Relationship, Path


INT64_MIN = -(2 ** 63)
INT64_MAX = (2 ** 63) - 1


class PackStreamHydrator(object):

    def __init__(self, protocol_version):
        from .graph import Graph, hydration_functions as graph_hydration_functions

        super(PackStreamHydrator, self).__init__()
        self.graph = Graph()
        self.hydration_functions = {}
        self.hydration_functions.update(graph_hydration_functions(self.graph))
        if protocol_version >= 2:
            from .spatial import hydration_functions as spatial_hydration_functions
            from .temporal import hydration_functions as temporal_hydration_functions
            self.hydration_functions.update(spatial_hydration_functions())
            self.hydration_functions.update(temporal_hydration_functions())

    def hydrate(self, values):
        """ Convert PackStream values into native values.
        """
        from neobolt.packstream import Structure

        def hydrate_(obj):
            if isinstance(obj, Structure):
                try:
                    f = self.hydration_functions[obj.tag]
                except KeyError:
                    # If we don't recognise the structure type, just return it as-is
                    return obj
                else:
                    return f(*map(hydrate_, obj.fields))
            elif isinstance(obj, list):
                return list(map(hydrate_, obj))
            elif isinstance(obj, dict):
                return {key: hydrate_(value) for key, value in obj.items()}
            else:
                return obj

        return tuple(map(hydrate_, values))

    def hydrate_records(self, keys, record_values):
        for values in record_values:
            yield Record(zip(keys, self.hydrate(values)))


class PackStreamDehydrator(object):

    def __init__(self, protocol_version, supports_bytes=False):
        from .graph import Graph, dehydration_functions as graph_dehydration_functions
        self.supports_bytes = supports_bytes
        self.dehydration_functions = {}
        self.dehydration_functions.update(graph_dehydration_functions())
        if protocol_version >= 2:
            from .spatial import dehydration_functions as spatial_dehydration_functions
            from .temporal import dehydration_functions as temporal_dehydration_functions
            self.dehydration_functions.update(spatial_dehydration_functions())
            self.dehydration_functions.update(temporal_dehydration_functions())

    def dehydrate(self, values):
        """ Convert native values into PackStream values.
        """

        def dehydrate_(obj):
            try:
                f = self.dehydration_functions[type(obj)]
            except KeyError:
                pass
            else:
                return f(obj)
            if obj is None:
                return None
            elif isinstance(obj, bool):
                return obj
            elif isinstance(obj, integer):
                if INT64_MIN <= obj <= INT64_MAX:
                    return obj
                raise ValueError("Integer out of bounds (64-bit signed integer values only)")
            elif isinstance(obj, float):
                return obj
            elif isinstance(obj, string):
                return ustr(obj)
            elif isinstance(obj, (bytes, bytearray)):  # order is important here - bytes must be checked after string
                if self.supports_bytes:
                    return obj
                else:
                    raise TypeError("This PackSteam channel does not support BYTES (consider upgrading to Neo4j 3.2+)")
            elif isinstance(obj, (list, map_type)):
                return list(map(dehydrate_, obj))
            elif isinstance(obj, dict):
                if any(not isinstance(key, string) for key in obj.keys()):
                    raise TypeError("Non-string dictionary keys are not supported")
                return {key: dehydrate_(value) for key, value in obj.items()}
            else:
                raise TypeError(obj)

        return tuple(map(dehydrate_, values))
