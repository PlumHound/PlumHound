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


__all__ = [
    "Packer",
    "Structure",
    "Unpacker",
]


from neobolt.meta import import_best


class Structure(object):

    def __init__(self, tag, *fields):
        self.tag = tag
        self.fields = list(fields)

    def __repr__(self):
        return "Structure<%s>(%s)" % (self.tag, ", ".join(map(repr, self.fields)))

    def __eq__(self, other):
        try:
            return self.tag == other.tag and self.fields == other.fields
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, key):
        return self.fields[key]

    def __setitem__(self, key, value):
        self.fields[key] = value


Packer = import_best("neobolt.packstream._packer", "neobolt.packstream.packer").Packer
Unpacker = import_best("neobolt.packstream._unpacker", "neobolt.packstream.unpacker").Unpacker
