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


from __future__ import unicode_literals

import logging
from argparse import ArgumentParser
from json import loads as json_loads
from sys import stdout, stderr

from neobolt.addressing import SocketAddress
from neobolt.diagnostics import Watcher
from neobolt.direct import connect, DEFAULT_PORT
from neobolt.exceptions import CypherError


def main():
    parser = ArgumentParser(description="Execute one or more Cypher statements using Bolt.")
    parser.add_argument("statement", nargs="+")
    parser.add_argument("-a", "--address", default="localhost:7687", metavar="ADDRESS")
    parser.add_argument("-k", "--keys", action="store_true")
    parser.add_argument("-P", "--password")
    parser.add_argument("-p", "--parameter", action="append", metavar="NAME=VALUE")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-s", "--secure", action="store_true")
    parser.add_argument("-U", "--user", default="neo4j")
    parser.add_argument("-v", "--verbose", action="count")
    parser.add_argument("-x", "--times", type=int, default=1)
    parser.add_argument("-z", "--summary", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        Watcher("neobolt").watch(logging.DEBUG, stderr)

    parameters = {}
    for parameter in args.parameter or []:
        name, _, value = parameter.partition("=")
        if value == "" and name in parameters:
            del parameters[name]
        else:
            try:
                parameters[name] = json_loads(value)
            except ValueError:
                parameters[name] = value

    cx = connect(SocketAddress.parse(args.address, DEFAULT_PORT), auth=(args.user, args.password), encrypted=args.secure)
    try:
        for _ in range(args.times):
            for statement in args.statement:
                metadata = {}
                records = []
                try:
                    cx.run(statement, parameters, on_success=metadata.update)
                    cx.pull_all(on_records=records.extend, on_success=metadata.update)
                    cx.sync()
                except CypherError as error:
                    stderr.write("%s: %s\r\n" % (error.code, error.message))
                else:
                    if not args.quiet:
                        if args.keys:
                            stdout.write("%s\r\n" % "\t".join(metadata.get("fields", ())))
                        for i, record in enumerate(records):
                            stdout.write("%s\r\n" % "\t".join(map(repr, record)))
                        if args.summary:
                            for key, value in sorted(metadata):
                                stdout.write("{}: {}\r\n".format(key, value))
                            stdout.write("\r\n")
    finally:
        cx.close()


if __name__ == "__main__":
    main()
