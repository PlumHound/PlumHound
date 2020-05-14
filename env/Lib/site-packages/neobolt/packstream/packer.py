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


from struct import pack as struct_pack

from neobolt.compat import integer, string
from neobolt.packstream import Structure


NULL_ = b"\xC0"
FALSE = b"\xC2"
TRUE = b"\xC3"

PACKED_UINT_8 = [struct_pack(">B", value) for value in range(0x100)]
PACKED_UINT_16 = [struct_pack(">H", value) for value in range(0x10000)]

UNPACKED_UINT_8 = {bytes(bytearray([x])): x for x in range(0x100)}
UNPACKED_UINT_16 = {struct_pack(">H", x): x for x in range(0x10000)}

UNPACKED_MARKERS = {NULL_: None, TRUE: True, FALSE: False}
UNPACKED_MARKERS.update({bytes(bytearray([z])): z for z in range(0x00, 0x80)})
UNPACKED_MARKERS.update({bytes(bytearray([z + 256])): z for z in range(-0x10, 0x00)})


INT64_HI = 2 ** 63
INT64_LO = -(2 ** 63)


class Packer(object):

    supports_bytes = False

    def __init__(self, stream):
        self.stream = stream
        self._write = self.stream.write

    def pack_raw(self, data):
        self._write(data)

    def pack(self, value):
        return self._pack(value)

    def _pack(self, value):
        write = self._write

        # None
        if value is None:
            write(b"\xC0")  # NULL

        # Boolean
        elif value is True:
            write(b"\xC3")
        elif value is False:
            write(b"\xC2")

        # Float (only double precision is supported)
        elif isinstance(value, float):
            write(b"\xC1")
            write(struct_pack(">d", value))

        # Integer
        elif isinstance(value, integer):
            if -0x10 <= value < 0x80:
                write(PACKED_UINT_8[value % 0x100])
            elif -0x80 <= value < -0x10:
                write(b"\xC8")
                write(PACKED_UINT_8[value % 0x100])
            elif -0x8000 <= value < 0x8000:
                write(b"\xC9")
                write(PACKED_UINT_16[value % 0x10000])
            elif -0x80000000 <= value < 0x80000000:
                write(b"\xCA")
                write(struct_pack(">i", value))
            elif INT64_LO <= value < INT64_HI:
                write(b"\xCB")
                write(struct_pack(">q", value))
            else:
                raise OverflowError("Integer %s out of range" % value)

        # String
        elif isinstance(value, string):
            if isinstance(value, bytes):
                value_bytes = value
            else:
                value_bytes = value.encode("utf-8")
            self.pack_string_header(len(value_bytes))
            self.pack_raw(value_bytes)

        # Bytes (deliberately listed after String since in
        # Python 2, bytes should be treated as a String)
        elif isinstance(value, bytes):
            self.pack_bytes_header(len(value))
            self.pack_raw(value)
        elif isinstance(value, bytearray):
            self.pack_bytes_header(len(value))
            self.pack_raw(bytes(value))

        # List
        elif isinstance(value, list):
            self.pack_list_header(len(value))
            for item in value:
                self._pack(item)

        # Map
        elif isinstance(value, dict):
            self.pack_map_header(len(value))
            for key, item in value.items():
                self._pack(key)
                self._pack(item)

        # Structure
        elif isinstance(value, Structure):
            self.pack_struct(value.tag, value.fields)

        # Other
        else:
            raise ValueError("Values of type %s are not supported" % type(value))

    def pack_bytes_header(self, size):
        if not self.supports_bytes:
            raise TypeError("This PackSteam channel does not support BYTES (consider upgrading to Neo4j 3.2+)")
        write = self._write
        if size < 0x100:
            write(b"\xCC")
            write(PACKED_UINT_8[size])
        elif size < 0x10000:
            write(b"\xCD")
            write(PACKED_UINT_16[size])
        elif size < 0x100000000:
            write(b"\xCE")
            write(struct_pack(">I", size))
        else:
            raise OverflowError("Bytes header size out of range")

    def pack_string_header(self, size):
        write = self._write
        if size == 0x00:
            write(b"\x80")
        elif size == 0x01:
            write(b"\x81")
        elif size == 0x02:
            write(b"\x82")
        elif size == 0x03:
            write(b"\x83")
        elif size == 0x04:
            write(b"\x84")
        elif size == 0x05:
            write(b"\x85")
        elif size == 0x06:
            write(b"\x86")
        elif size == 0x07:
            write(b"\x87")
        elif size == 0x08:
            write(b"\x88")
        elif size == 0x09:
            write(b"\x89")
        elif size == 0x0A:
            write(b"\x8A")
        elif size == 0x0B:
            write(b"\x8B")
        elif size == 0x0C:
            write(b"\x8C")
        elif size == 0x0D:
            write(b"\x8D")
        elif size == 0x0E:
            write(b"\x8E")
        elif size == 0x0F:
            write(b"\x8F")
        elif size < 0x100:
            write(b"\xD0")
            write(PACKED_UINT_8[size])
        elif size < 0x10000:
            write(b"\xD1")
            write(PACKED_UINT_16[size])
        elif size < 0x100000000:
            write(b"\xD2")
            write(struct_pack(">I", size))
        else:
            raise OverflowError("String header size out of range")

    def pack_list_header(self, size):
        write = self._write
        if size == 0x00:
            write(b"\x90")
        elif size == 0x01:
            write(b"\x91")
        elif size == 0x02:
            write(b"\x92")
        elif size == 0x03:
            write(b"\x93")
        elif size == 0x04:
            write(b"\x94")
        elif size == 0x05:
            write(b"\x95")
        elif size == 0x06:
            write(b"\x96")
        elif size == 0x07:
            write(b"\x97")
        elif size == 0x08:
            write(b"\x98")
        elif size == 0x09:
            write(b"\x99")
        elif size == 0x0A:
            write(b"\x9A")
        elif size == 0x0B:
            write(b"\x9B")
        elif size == 0x0C:
            write(b"\x9C")
        elif size == 0x0D:
            write(b"\x9D")
        elif size == 0x0E:
            write(b"\x9E")
        elif size == 0x0F:
            write(b"\x9F")
        elif size < 0x100:
            write(b"\xD4")
            write(PACKED_UINT_8[size])
        elif size < 0x10000:
            write(b"\xD5")
            write(PACKED_UINT_16[size])
        elif size < 0x100000000:
            write(b"\xD6")
            write(struct_pack(">I", size))
        else:
            raise OverflowError("List header size out of range")

    def pack_list_stream_header(self):
        self._write(b"\xD7")

    def pack_map_header(self, size):
        write = self._write
        if size == 0x00:
            write(b"\xA0")
        elif size == 0x01:
            write(b"\xA1")
        elif size == 0x02:
            write(b"\xA2")
        elif size == 0x03:
            write(b"\xA3")
        elif size == 0x04:
            write(b"\xA4")
        elif size == 0x05:
            write(b"\xA5")
        elif size == 0x06:
            write(b"\xA6")
        elif size == 0x07:
            write(b"\xA7")
        elif size == 0x08:
            write(b"\xA8")
        elif size == 0x09:
            write(b"\xA9")
        elif size == 0x0A:
            write(b"\xAA")
        elif size == 0x0B:
            write(b"\xAB")
        elif size == 0x0C:
            write(b"\xAC")
        elif size == 0x0D:
            write(b"\xAD")
        elif size == 0x0E:
            write(b"\xAE")
        elif size == 0x0F:
            write(b"\xAF")
        elif size < 0x100:
            write(b"\xD8")
            write(PACKED_UINT_8[size])
        elif size < 0x10000:
            write(b"\xD9")
            write(PACKED_UINT_16[size])
        elif size < 0x100000000:
            write(b"\xDA")
            write(struct_pack(">I", size))
        else:
            raise OverflowError("Map header size out of range")

    def pack_map_stream_header(self):
        self._write(b"\xDB")

    def pack_struct(self, signature, fields):
        if len(signature) != 1 or not isinstance(signature, bytes):
            raise ValueError("Structure signature must be a single byte value")
        write = self._write
        size = len(fields)
        if size == 0x00:
            write(b"\xB0")
        elif size == 0x01:
            write(b"\xB1")
        elif size == 0x02:
            write(b"\xB2")
        elif size == 0x03:
            write(b"\xB3")
        elif size == 0x04:
            write(b"\xB4")
        elif size == 0x05:
            write(b"\xB5")
        elif size == 0x06:
            write(b"\xB6")
        elif size == 0x07:
            write(b"\xB7")
        elif size == 0x08:
            write(b"\xB8")
        elif size == 0x09:
            write(b"\xB9")
        elif size == 0x0A:
            write(b"\xBA")
        elif size == 0x0B:
            write(b"\xBB")
        elif size == 0x0C:
            write(b"\xBC")
        elif size == 0x0D:
            write(b"\xBD")
        elif size == 0x0E:
            write(b"\xBE")
        elif size == 0x0F:
            write(b"\xBF")
        elif size < 0x100:
            write(b"\xDC")
            write(PACKED_UINT_8[size])
        elif size < 0x10000:
            write(b"\xDD")
            write(PACKED_UINT_16[size])
        else:
            raise OverflowError("Structure size out of range")
        write(signature)
        for field in fields:
            self._pack(field)

    def pack_end_of_stream(self):
        self._write(b"\xDF")
