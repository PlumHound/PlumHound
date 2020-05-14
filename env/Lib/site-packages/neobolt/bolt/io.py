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


from struct import pack as struct_pack, unpack as struct_unpack

from neobolt.compat import memoryview_at


_empty_view = memoryview(b"")


class MessageFrame(object):

    _current_pane = -1
    _current_offset = -1

    def __init__(self, view, panes):
        self._view = view
        self._panes = panes
        if panes:
            self._current_pane = 0
            self._current_offset = 0

    def close(self):
         self._view = None

    def _next_pane(self):
        self._current_pane += 1
        if self._current_pane < len(self._panes):
            self._current_offset = 0
        else:
            self._current_pane = -1
            self._current_offset = -1

    def panes(self):
        return self._panes

    def read_int(self):
        if self._current_pane == -1:
            return -1
        p, q = self._panes[self._current_pane]
        size = q - p
        value = memoryview_at(self._view, p + self._current_offset)
        self._current_offset += 1
        if self._current_offset == size:
            self._next_pane()
        return value

    def read(self, n):
        if n == 0 or self._current_pane == -1:
            return _empty_view
        value = None
        is_memoryview = False
        offset = 0

        to_read = n
        while to_read > 0 and self._current_pane >= 0:
            p, q = self._panes[self._current_pane]
            size = q - p
            remaining = size - self._current_offset
            start = p + self._current_offset
            if to_read <= remaining:
                end = start + to_read
                if to_read < remaining:
                    self._current_offset += to_read
                else:
                    self._next_pane()
            else:
                end = q
                self._next_pane()

            read = end - start
            if value:
                if is_memoryview:
                    new_value = bytearray(n)
                    new_value[:offset] = value[:offset]
                    value = new_value
                    is_memoryview = False
                value[offset:offset+read] = self._view[start:end]
            else:
                value = memoryview(self._view[start:end])
                is_memoryview = True
            offset += read
            to_read -= read
        return memoryview(value)


class ChunkedInputBuffer(object):

    def __init__(self, capacity=524288):
        self._data = bytearray(capacity)
        self._view = memoryview(self._data)
        self._extent = 0    # end position of all loaded data
        self._origin = 0    # start position of current frame
        self._limit = -1    # end position of current frame
        self._frame = None  # frame object

    def __repr__(self):
        return repr(self.view().tobytes())

    def capacity(self):
        return len(self._view)

    def view(self):
        return memoryview(self._view[:self._extent])

    def load(self, b):
        """

        Note: may modify buffer size
        """
        n = len(b)
        new_extent = self._extent + n
        overflow = new_extent - len(self._data)
        if overflow > 0:
            if self._recycle():
                return self.load(b)
            self._view = None
            new_extent = self._extent + n
            self._data[self._extent:new_extent] = b
            self._view = memoryview(self._data)
        else:
            self._view[self._extent:new_extent] = b
        self._extent = new_extent

    def receive(self, socket, n):
        """

        Note: may modify buffer size, should error if frame exists
        """
        try:
            new_extent = self._extent + n
            overflow = new_extent - len(self._data)
            if overflow > 0:
                if self._recycle():
                    return self.receive(socket, n)
                self._view = None
                data = socket.recv(n)
                data_size = len(data)
                new_extent = self._extent + data_size
                self._data[self._extent:new_extent] = data
                self._view = memoryview(self._data)
            else:
                data_size = socket.recv_into(self._view[self._extent:new_extent])
                new_extent = self._extent + data_size
            self._extent = new_extent
            return data_size
        except (IOError, OSError):  # TODO 2.0: remove IOError
            return 0
        except KeyboardInterrupt:
            return -1

    def receive_message(self, socket, n):
        """

        :param socket:
        :param n:
        :return:
        """
        while not self.frame_message():
            received = self.receive(socket, n)
            if received <= 0:
                return received
        return 1

    def _recycle(self):
        """ Reclaim buffer space before the origin.

        Note: modifies buffer size
        """
        origin = self._origin
        if origin == 0:
            return False
        available = self._extent - origin
        self._data[:available] = self._data[origin:self._extent]
        self._extent = available
        self._origin = 0
        #log_debug("Recycled %d bytes" % origin)
        return True

    def frame(self):
        return self._frame

    def frame_message(self):
        """ Construct a frame around the first complete message in the buffer.
        """
        if self._frame is not None:
            self.discard_message()
        panes = []
        p = origin = self._origin
        extent = self._extent
        while p < extent:
            available = extent - p
            if available < 2:
                break
            chunk_size, = struct_unpack(">H", self._view[p:(p + 2)])
            p += 2
            if chunk_size == 0:
                self._limit = p
                self._frame = MessageFrame(memoryview(self._view[origin:self._limit]), panes)
                return True
            q = p + chunk_size
            panes.append((p - origin, q - origin))
            p = q
        return False

    def discard_message(self):
        if self._frame is not None:
            self._frame.close()
            self._origin = self._limit
            self._limit = -1
            self._frame = None


class ChunkedOutputBuffer(object):

    def __init__(self, capacity=1048576, max_chunk_size=16384):
        self._max_chunk_size = max_chunk_size
        self._header = 0
        self._start = 2
        self._end = 2
        self._data = bytearray(capacity)

    def max_chunk_size(self):
        return self._max_chunk_size

    def clear(self):
        self._header = 0
        self._start = 2
        self._end = 2
        self._data[0:2] = b"\x00\x00"

    def write(self, b):
        to_write = len(b)
        max_chunk_size = self._max_chunk_size
        pos = 0
        while to_write > 0:
            chunk_size = self._end - self._start
            remaining = max_chunk_size - chunk_size
            if remaining == 0 or remaining < to_write <= max_chunk_size:
                self.chunk()
            else:
                wrote = min(to_write, remaining)
                new_end = self._end + wrote
                self._data[self._end:new_end] = b[pos:pos+wrote]
                self._end = new_end
                pos += wrote
                new_chunk_size = self._end - self._start
                self._data[self._header:(self._header + 2)] = struct_pack(">H", new_chunk_size)
                to_write -= wrote

    def chunk(self):
        self._header = self._end
        self._start = self._header + 2
        self._end = self._start
        self._data[self._header:self._start] = b"\x00\x00"

    def view(self):
        end = self._end
        chunk_size = end - self._start
        if chunk_size == 0:
            return memoryview(self._data[:self._header])
        else:
            return memoryview(self._data[:end])
