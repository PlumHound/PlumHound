#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound
# License GNU GPL3

# Python Libraries
import ast
import csv
from tabulate import tabulate
import json

# Plumhound Modules
from lib.phLoggy import loggy, log_calls


@log_calls
def send_it_out(verbose, keys_list, results_list, out_format, out_file, out_path, title):
    # Quick fix if keys returned no records to properly rebuild the keys list of 0, instead of int(0)
    if isinstance(keys_list, int):
        raise 'oh no'
        keys_list = []
    output = ""

    path = out_path + out_file

    if out_format == "CSV":
        loggy(100, "Beginning Output CSV:" + path)
        with open(path, "w", newline="") as f:
            loggy(500, "KeyType: " + str(type(keys_list)))
            loggy(500, "KeyList: " + str((keys_list)))
            writer = csv.writer(f)
            ModKeyList = ast.literal_eval("[" + str(keys_list) + "]")
            loggy(500, "KeyTypeMod: " + str(type(ModKeyList)))
            loggy(500, "KeyListMod: " + str(ModKeyList))
            writer.writerows(ModKeyList)
            loggy(500, "ResultsType: " + str(type(results_list)))
            loggy(999, "ResultsList: " + str(results_list))
            writer.writerows(results_list)
        return True

    if out_format == "STDOUT":
        print()
        output = tabulate(results_list, keys_list, tablefmt="simple")
        print(output)
        return True

    if out_format == "JSON":
        fsys = open(path, "w")
        fsys.write(json.dumps({"keys": keys_list, "results": results_list}))
        fsys.close()
        return True
