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


from __future__ import division


"""
This module defines temporal data types.
"""

from datetime import date, time, datetime, timedelta

from neotime import Duration, Date, Time, DateTime
from pytz import FixedOffset, timezone, utc

from neobolt.packstream import Structure


UNIX_EPOCH_DATE = Date(1970, 1, 1)
UNIX_EPOCH_DATE_ORDINAL = UNIX_EPOCH_DATE.to_ordinal()
UNIX_EPOCH_DATETIME_UTC = DateTime(1970, 1, 1, 0, 0, 0, utc)


def hydrate_date(days):
    """ Hydrator for `Date` values.

    :param days:
    :return: Date
    """
    return Date.from_ordinal(UNIX_EPOCH_DATE_ORDINAL + days)


def dehydrate_date(value):
    """ Dehydrator for `date` values.

    :param value:
    :type value: Date
    :return:
    """
    return Structure(b"D", value.toordinal() - UNIX_EPOCH_DATE.toordinal())


def hydrate_time(nanoseconds, tz=None):
    """ Hydrator for `Time` and `LocalTime` values.

    :param nanoseconds:
    :param tz:
    :return: Time
    """
    seconds, nanoseconds = map(int, divmod(nanoseconds, 1000000000))
    minutes, seconds = map(int, divmod(seconds, 60))
    hours, minutes = map(int, divmod(minutes, 60))
    seconds = (1000000000 * seconds + nanoseconds) / 1000000000
    t = Time(hours, minutes, seconds)
    if tz is None:
        return t
    tz_offset_minutes, tz_offset_seconds = divmod(tz, 60)
    zone = FixedOffset(tz_offset_minutes)
    return zone.localize(t)


def dehydrate_time(value):
    """ Dehydrator for `time` values.

    :param value:
    :type value: Time
    :return:
    """
    if isinstance(value, Time):
        nanoseconds = int(value.ticks * 1000000000)
    elif isinstance(value, time):
        nanoseconds = (3600000000000 * value.hour + 60000000000 * value.minute +
                       1000000000 * value.second + 1000 * value.microsecond)
    else:
        raise TypeError("Value must be a neotime.Time or a datetime.time")
    if value.tzinfo:
        return Structure(b"T", nanoseconds, value.tzinfo.utcoffset(value).seconds)
    else:
        return Structure(b"t", nanoseconds)


def hydrate_datetime(seconds, nanoseconds, tz=None):
    """ Hydrator for `DateTime` and `LocalDateTime` values.

    :param seconds:
    :param nanoseconds:
    :param tz:
    :return: datetime
    """
    minutes, seconds = map(int, divmod(seconds, 60))
    hours, minutes = map(int, divmod(minutes, 60))
    days, hours = map(int, divmod(hours, 24))
    seconds = (1000000000 * seconds + nanoseconds) / 1000000000
    t = DateTime.combine(Date.from_ordinal(UNIX_EPOCH_DATE_ORDINAL + days), Time(hours, minutes, seconds))
    if tz is None:
        return t
    if isinstance(tz, int):
        tz_offset_minutes, tz_offset_seconds = divmod(tz, 60)
        zone = FixedOffset(tz_offset_minutes)
    else:
        zone = timezone(tz)
    return zone.localize(t)


def dehydrate_datetime(value):
    """ Dehydrator for `datetime` values.

    :param value:
    :type value: datetime
    :return:
    """

    def seconds_and_nanoseconds(dt):
        if isinstance(dt, datetime):
            dt = DateTime.from_native(dt)
        zone_epoch = DateTime(1970, 1, 1, tzinfo=dt.tzinfo)
        t = dt.to_clock_time() - zone_epoch.to_clock_time()
        return t.seconds, t.nanoseconds

    tz = value.tzinfo
    if tz is None:
        # without time zone
        value = utc.localize(value)
        seconds, nanoseconds = seconds_and_nanoseconds(value)
        return Structure(b"d", seconds, nanoseconds)
    elif hasattr(tz, "zone") and tz.zone:
        # with named time zone
        seconds, nanoseconds = seconds_and_nanoseconds(value)
        return Structure(b"f", seconds, nanoseconds, tz.zone)
    else:
        # with time offset
        seconds, nanoseconds = seconds_and_nanoseconds(value)
        return Structure(b"F", seconds, nanoseconds, tz.utcoffset(value).seconds)


def hydrate_duration(months, days, seconds, nanoseconds):
    """ Hydrator for `Duration` values.

    :param months:
    :param days:
    :param seconds:
    :param nanoseconds:
    :return: `duration` namedtuple
    """
    return Duration(months=months, days=days, seconds=seconds, nanoseconds=nanoseconds)


def dehydrate_duration(value):
    """ Dehydrator for `duration` values.

    :param value:
    :type value: Duration
    :return:
    """
    return Structure(b"E", value.months, value.days, value.seconds, int(1000000000 * value.subseconds))


def dehydrate_timedelta(value):
    """ Dehydrator for `timedelta` values.

    :param value:
    :type value: timedelta
    :return:
    """
    months = 0
    days = value.days
    seconds = value.seconds
    nanoseconds = 1000 * value.microseconds
    return Structure(b"E", months, days, seconds, nanoseconds)


__hydration_functions = {
    b"D": hydrate_date,
    b"T": hydrate_time,         # time zone offset
    b"t": hydrate_time,         # no time zone
    b"F": hydrate_datetime,     # time zone offset
    b"f": hydrate_datetime,     # time zone name
    b"d": hydrate_datetime,     # no time zone
    b"E": hydrate_duration,
}

# TODO: re-add built-in types
__dehydration_functions = {
    Date: dehydrate_date,
    date: dehydrate_date,
    Time: dehydrate_time,
    time: dehydrate_time,
    DateTime: dehydrate_datetime,
    datetime: dehydrate_datetime,
    Duration: dehydrate_duration,
    timedelta: dehydrate_timedelta,
}


def hydration_functions():
    return __hydration_functions


def dehydration_functions():
    return __dehydration_functions
