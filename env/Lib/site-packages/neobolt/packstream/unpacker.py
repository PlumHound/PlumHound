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


from codecs import decode
from struct import unpack as struct_unpack

from neobolt.packstream import Structure


EndOfStream = object()


class Unpacker(object):

    def __init__(self):
        self.source = None

    def attach(self, source):
        self.source = source

    def read(self, n=1):
        return self.source.read(n)

    def read_int(self):
        return self.source.read_int()

    def unpack(self):
        return self._unpack()

    def _unpack(self):
        marker = self.read_int()

        if marker == -1:
            raise RuntimeError("Nothing to unpack")

        # Tiny Integer
        if 0x00 <= marker <= 0x7F:
            return marker
        elif 0xF0 <= marker <= 0xFF:
            return marker - 0x100

        # Null
        elif marker == 0xC0:
            return None

        # Float
        elif marker == 0xC1:
            value, = struct_unpack(">d", self.read(8))
            return value

        # Boolean
        elif marker == 0xC2:
            return False
        elif marker == 0xC3:
            return True

        # Integer
        elif marker == 0xC8:
            return struct_unpack(">b", self.read(1))[0]
        elif marker == 0xC9:
            return struct_unpack(">h", self.read(2))[0]
        elif marker == 0xCA:
            return struct_unpack(">i", self.read(4))[0]
        elif marker == 0xCB:
            return struct_unpack(">q", self.read(8))[0]

        # Bytes
        elif marker == 0xCC:
            size, = struct_unpack(">B", self.read(1))
            return self.read(size).tobytes()
        elif marker == 0xCD:
            size, = struct_unpack(">H", self.read(2))
            return self.read(size).tobytes()
        elif marker == 0xCE:
            size, = struct_unpack(">I", self.read(4))
            return self.read(size).tobytes()

        else:
            marker_high = marker & 0xF0
            # String
            if marker_high == 0x80:  # TINY_STRING
                return decode(self.read(marker & 0x0F), "utf-8")
            elif marker == 0xD0:  # STRING_8:
                size, = struct_unpack(">B", self.read(1))
                return decode(self.read(size), "utf-8")
            elif marker == 0xD1:  # STRING_16:
                size, = struct_unpack(">H", self.read(2))
                return decode(self.read(size), "utf-8")
            elif marker == 0xD2:  # STRING_32:
                size, = struct_unpack(">I", self.read(4))
                return decode(self.read(size), "utf-8")

            # List
            elif 0x90 <= marker <= 0x9F or 0xD4 <= marker <= 0xD7:
                return self._unpack_list(marker)

            # Map
            elif 0xA0 <= marker <= 0xAF or 0xD8 <= marker <= 0xDB:
                return self._unpack_map(marker)

            # Structure
            elif 0xB0 <= marker <= 0xBF or 0xDC <= marker <= 0xDD:
                size, tag = self._unpack_structure_header(marker)
                value = Structure(tag, *([None] * size))
                for i in range(len(value)):
                    value[i] = self._unpack()
                return value

            elif marker == 0xDF:  # END_OF_STREAM:
                return EndOfStream

            else:
                raise RuntimeError("Unknown PackStream marker %02X" % marker)

    def unpack_list(self):
        marker = self.read_int()
        return self._unpack_list(marker)

    def _unpack_list(self, marker):
        marker_high = marker & 0xF0
        if marker_high == 0x90:
            size = marker & 0x0F
            if size == 0:
                return []
            elif size == 1:
                return [self._unpack()]
            else:
                return [self._unpack() for _ in range(size)]
        elif marker == 0xD4:  # LIST_8:
            size, = struct_unpack(">B", self.read(1))
            return [self._unpack() for _ in range(size)]
        elif marker == 0xD5:  # LIST_16:
            size, = struct_unpack(">H", self.read(2))
            return [self._unpack() for _ in range(size)]
        elif marker == 0xD6:  # LIST_32:
            size, = struct_unpack(">I", self.read(4))
            return [self._unpack() for _ in range(size)]
        elif marker == 0xD7:  # LIST_STREAM:
            value = []
            item = None
            while item is not EndOfStream:
                item = self._unpack()
                if item is not EndOfStream:
                    value.append(item)
            return value
        else:
            return None

    def unpack_map(self):
        marker = self.read_int()
        return self._unpack_map(marker)

    def _unpack_map(self, marker):
        marker_high = marker & 0xF0
        if marker_high == 0xA0:
            size = marker & 0x0F
            value = {}
            for _ in range(size):
                key = self._unpack()
                value[key] = self._unpack()
            return value
        elif marker == 0xD8:  # MAP_8:
            size, = struct_unpack(">B", self.read(1))
            value = {}
            for _ in range(size):
                key = self._unpack()
                value[key] = self._unpack()
            return value
        elif marker == 0xD9:  # MAP_16:
            size, = struct_unpack(">H", self.read(2))
            value = {}
            for _ in range(size):
                key = self._unpack()
                value[key] = self._unpack()
            return value
        elif marker == 0xDA:  # MAP_32:
            size, = struct_unpack(">I", self.read(4))
            value = {}
            for _ in range(size):
                key = self._unpack()
                value[key] = self._unpack()
            return value
        elif marker == 0xDB:  # MAP_STREAM:
            value = {}
            key = None
            while key is not EndOfStream:
                key = self._unpack()
                if key is not EndOfStream:
                    value[key] = self._unpack()
            return value
        else:
            return None

    def unpack_structure_header(self):
        marker = self.read_int()
        if marker == -1:
            return None, None
        else:
            return self._unpack_structure_header(marker)

    def _unpack_structure_header(self, marker):
        marker_high = marker & 0xF0
        if marker_high == 0xB0:  # TINY_STRUCT
            signature = self.read(1).tobytes()
            return marker & 0x0F, signature
        elif marker == 0xDC:  # STRUCT_8:
            size, = struct_unpack(">B", self.read(1))
            signature = self.read(1).tobytes()
            return size, signature
        elif marker == 0xDD:  # STRUCT_16:
            size, = struct_unpack(">H", self.read(2))
            signature = self.read(1).tobytes()
            return size, signature
        else:
            raise RuntimeError("Expected structure, found marker %02X" % marker)
