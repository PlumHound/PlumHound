#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound
# License GNU GPL3

# Python Libraries
import csv
from tabulate import tabulate
import json

# Plumhound Modules
from lib.phLoggy import loggy, log_calls


@log_calls
def send_it_out(verbose, results, out_format, out_file, out_path, title, task_type):
    output = ""

    path = out_path + out_file

    if out_format == "CSV":
        if task_type != 'query':
            raise Exception('Can not create CSV for tasks other than query')
        keys = results['keys']
        loggy(100, "Beginning Output CSV:" + path)
        with open(path, "w", newline="") as f:
            loggy(500, "KeyType: " + str(type(keys)))
            loggy(500, "KeyList: " + str((keys)))
            writer = csv.writer(f)
            writer.writerows(keys)
            loggy(500, "ResultsType: " + str(type(results['result'])))
            loggy(999, "ResultsList: " + str(results['result']))
            writer.writerows(results['result'])
        return True

    if out_format == "STDOUT":
        print()
        if task_type == 'query':
            print(tabulate(results['result'], results['keys'], tablefmt="simple"))
        else:
            print(results)
        return True

    if out_format == "JSON":
        fsys = open(path, "w")
        fsys.write(json.dumps(results))
        fsys.close()
        return True
