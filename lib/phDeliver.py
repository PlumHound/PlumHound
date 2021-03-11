#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound
# License GNU GPL3

# Python Libraries
# import csv
from tabulate import tabulate
import json

# Plumhound Modules
from lib.phLoggy import log_calls


@log_calls
def send_it_out(verbose, report):
    results = report['tasks']
    out_format = report['format']
    out_path = report['path']
    title = report['name']

    if out_format == "STDOUT":
        for result in results:
            print(f"{title}: ")
            if result['type'] == 'query':
                print(tabulate(result['results']['results'], result['keys'], tablefmt="simple"))
            else:
                print(results)
        return True

    if out_format == "JSON":
        print('writing out!')
        fsys = open(out_path, "w")
        fsys.write(json.dumps(results))
        fsys.close()
        return True
