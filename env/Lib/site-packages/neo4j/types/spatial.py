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
This module defines spatial data types.
"""


from neobolt.packstream import Structure


__all__ = [
    "Point",
    "CartesianPoint",
    "WGS84Point",
]


# SRID to subclass mappings
__srid_table = {}


class Point(tuple):
    """ A point within a geometric space. This type is generally used
    via its subclasses and should not be instantiated directly unless
    there is no subclass defined for the required SRID.
    """

    srid = None

    def __new__(cls, iterable):
        return tuple.__new__(cls, iterable)

    def __repr__(self):
        return "POINT(%s)" % " ".join(map(str, self))

    def __eq__(self, other):
        try:
            return type(self) is type(other) and tuple(self) == tuple(other)
        except (AttributeError, TypeError):
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(type(self)) ^ hash(tuple(self))


def __point_subclass(name, fields, srid_map):
    """ Dynamically create a Point subclass.
    """

    def srid(self):
        try:
            return srid_map[len(self)]
        except KeyError:
            return None

    attributes = {"srid": property(srid)}

    for index, subclass_field in enumerate(fields):

        def accessor(self, i=index, f=subclass_field):
            try:
                return self[i]
            except IndexError:
                raise AttributeError(f)

        for field_alias in {subclass_field, "xyz"[index]}:
            attributes[field_alias] = property(accessor)

    cls = type(name, (Point,), attributes)

    for dim, srid in srid_map.items():
        __srid_table[srid] = (cls, dim)

    return cls


# Point subclass definitions
CartesianPoint = __point_subclass("CartesianPoint", ["x", "y", "z"], {2: 7203, 3: 9157})
WGS84Point = __point_subclass("WGS84Point", ["longitude", "latitude", "height"], {2: 4326, 3: 4979})


def hydrate_point(srid, *coordinates):
    """ Create a new instance of a Point subclass from a raw
    set of fields. The subclass chosen is determined by the
    given SRID; a ValueError will be raised if no such
    subclass can be found.
    """
    try:
        point_class, dim = __srid_table[srid]
    except KeyError:
        point = Point(coordinates)
        point.srid = srid
        return point
    else:
        if len(coordinates) != dim:
            raise ValueError("SRID %d requires %d coordinates (%d provided)" % (srid, dim, len(coordinates)))
        return point_class(coordinates)


def dehydrate_point(value):
    """ Dehydrator for Point data.

    :param value:
    :type value: Point
    :return:
    """
    dim = len(value)
    if dim == 2:
        return Structure(b"X", value.srid, *value)
    elif dim == 3:
        return Structure(b"Y", value.srid, *value)
    else:
        raise ValueError("Cannot dehydrate Point with %d dimensions" % dim)


__hydration_functions = {
    b"X": hydrate_point,
    b"Y": hydrate_point,
}

__dehydration_functions = {
    Point: dehydrate_point,
}
__dehydration_functions.update({cls: dehydrate_point for cls in Point.__subclasses__()})


def hydration_functions():
    return __hydration_functions


def dehydration_functions():
    return __dehydration_functions
