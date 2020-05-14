#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2002-2018 "Neo4j,"
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


class DateType(type):

    def __getattr__(cls, name):
        try:
            return {
                "fromisoformat": cls.from_iso_format,
                "fromordinal": cls.from_ordinal,
                "fromtimestamp": cls.from_timestamp,
                "utcfromtimestamp": cls.utc_from_timestamp,
            }[name]
        except KeyError:
            raise AttributeError("%s has no attribute %r" % (cls.__name__, name))


class TimeType(type):

    def __getattr__(cls, name):
        try:
            return {
                "fromisoformat": cls.from_iso_format,
                "utcnow": cls.utc_now,
            }[name]
        except KeyError:
            raise AttributeError("%s has no attribute %r" % (cls.__name__, name))


class DateTimeType(type):

    def __getattr__(cls, name):
        try:
            return {
                "fromisoformat": cls.from_iso_format,
                "fromordinal": cls.from_ordinal,
                "fromtimestamp": cls.from_timestamp,
                "strptime": cls.parse,
                "today": cls.now,
                "utcfromtimestamp": cls.utc_from_timestamp,
                "utcnow": cls.utc_now,
            }[name]
        except KeyError:
            raise AttributeError("%s has no attribute %r" % (cls.__name__, name))
