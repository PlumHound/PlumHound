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
This module provides compatibility functions between different versions
and flavours of Python. It is separate for clarity and deliberately
excluded from test coverage.
"""


map_type = type(map(str, range(0)))

# Workaround for Python 2/3 type differences
try:
    unicode
except NameError:
    # Python 3

    integer = int
    string = str
    unicode = str
    unichr = chr

    def bstr(x):
        if isinstance(x, bytes):
            return x
        elif isinstance(x, str):
            return x.encode("utf-8")
        else:
            return str(x).encode("utf-8")

    def ustr(x):
        if isinstance(x, bytes):
            return x.decode("utf-8")
        elif isinstance(x, str):
            return x
        else:
            return str(x)

    xstr = ustr

    def memoryview_at(view, index):
        return view[index]

else:
    # Python 2

    integer = (int, long)
    string = (str, unicode)
    unicode = unicode
    unichr = unichr

    def bstr(x):
        if isinstance(x, str):
            return x
        elif isinstance(x, unicode):
            return x.encode("utf-8")
        else:
            return unicode(x).encode("utf-8")

    def ustr(x):
        if isinstance(x, str):
            return x.decode("utf-8")
        elif isinstance(x, unicode):
            return x
        else:
            return unicode(x)

    xstr = bstr

    def memoryview_at(view, index):
        return ord(view[index])

try:
    from multiprocessing import Array, Process
except ImportError:
    # Workaround for Jython

    from array import array
    from threading import Thread as Process

    def Array(typecode, size):
        return array(typecode, [0] * size)


# Obtain a performance timer - this varies by platform and
# Jython support is even more tricky as the standard timer
# does not support nanoseconds. The combination below
# works with Python 2, Python 3 and Jython.
try:
    from java.lang.System import nanoTime
except ImportError:
    JYTHON = False

    try:
        from time import perf_counter
    except ImportError:
        from time import time as perf_counter
else:
    JYTHON = True

    def perf_counter():
        return nanoTime() / 1000000000


# Using or importing the ABCs from 'collections' instead of from
# 'collections.abc' is deprecated, and in 3.8 it will stop working
try:
    from collections.abc import Sequence, Mapping
except ImportError:
    from collections import Sequence, Mapping


# The location of urlparse varies between Python 2 and 3
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


def deprecated(message):
    """ Decorator for deprecating functions and methods.

    ::

        @deprecated("'foo' has been deprecated in favour of 'bar'")
        def foo(x):
            pass

    """
    def f__(f):
        def f_(*args, **kwargs):
            from warnings import warn
            warn(message, category=DeprecationWarning, stacklevel=2)
            return f(*args, **kwargs)
        f_.__name__ = f.__name__
        f_.__doc__ = f.__doc__
        f_.__dict__.update(f.__dict__)
        return f_
    return f__
