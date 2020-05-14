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


from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, Formatter, StreamHandler, getLogger
from sys import stdout


class ColourFormatter(Formatter):
    """ Colour formatter for pretty log output.
    """

    def format(self, record):
        s = super(ColourFormatter, self).format(record)
        if record.levelno == CRITICAL:
            return "\x1b[31;1m%s\x1b[0m" % s  # bright red
        elif record.levelno == ERROR:
            return "\x1b[33;1m%s\x1b[0m" % s  # bright yellow
        elif record.levelno == WARNING:
            return "\x1b[33m%s\x1b[0m" % s    # yellow
        elif record.levelno == INFO:
            return "\x1b[37m%s\x1b[0m" % s    # white
        elif record.levelno == DEBUG:
            return "\x1b[36m%s\x1b[0m" % s    # cyan
        else:
            return s


class Watcher(object):
    """ Log watcher for monitoring driver and protocol activity.
    """

    handlers = {}

    def __init__(self, logger_name):
        super(Watcher, self).__init__()
        self.logger_name = logger_name
        self.logger = getLogger(self.logger_name)
        self.formatter = ColourFormatter("%(asctime)s  %(message)s")

    def __enter__(self):
        self.watch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def watch(self, level=DEBUG, out=stdout):
        self.stop()
        handler = StreamHandler(out)
        handler.setFormatter(self.formatter)
        self.handlers[self.logger_name] = handler
        self.logger.addHandler(handler)
        self.logger.setLevel(level)

    def stop(self):
        try:
            self.logger.removeHandler(self.handlers[self.logger_name])
        except KeyError:
            pass


def watch(logger_name, level=DEBUG, out=stdout):
    """ Quick wrapper for using the Watcher.

    :param logger_name: name of logger to watch
    :param level: minimum log level to show (default INFO)
    :param out: where to send output (default stdout)
    :return: Watcher instance
    """
    watcher = Watcher(logger_name)
    watcher.watch(level, out)
    return watcher
