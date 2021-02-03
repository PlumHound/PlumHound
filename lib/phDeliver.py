#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Python Libraries
import ast
import csv
from tabulate import tabulate
from datetime import date
import json

# Plumhound Modules
from lib.phLoggy import loggy, log_calls


@log_calls
def send_it_out(verbose, keys_list, results_list, out_format, out_file, out_path, title, html_header, html_footer, html_css):
    # Quick fix if keys returned no records to properly rebuild the keys list of 0, instead of int(0)
    if isinstance(keys_list, int):
        raise 'oh no'
        keys_list = []
    output = ""

    if out_format == "CSV":
        loggy(100, "Beginning Output CSV:" + out_path + out_file)
        with open(out_path + out_file, "w", newline="") as f:
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
        fsys = open(out_path + out_file, "w")
        fsys.write(json.dumps({"keys": keys_list, "results": results_list}))
        fsys.close()
        return True

    if out_format == "HTML":
        loggy(100, "Beginning Output HTML:" + out_file)

        output = tabulate(results_list, keys_list, tablefmt="html")
        HTMLCSS_str = ""
        HTMLHeader_str = ""
        HTMLFooter_str = ""
        HTMLPre_str = "<HTML><head>"
        HTMLMId_str = "</head><Body>"
        HTMLEnd_str = "</body></html>"
        if html_header:
            with open(html_header, 'r') as header:
                HTMLHeader_str = header.read()
            HTMLHeader_str = replace_html_report_vars(HTMLHeader_str, title)

        if html_footer:
            with open(html_footer, 'r') as footer:
                HTMLFooter_str = footer.read()
            HTMLFooter_str = replace_html_report_vars(HTMLFooter_str, title)

        if html_css:
            with open(html_css, 'r') as css:
                HTMLCSS_str = "<style>\n" + css.read() + "\n</style>"

        loggy(500, "File Writing " + out_path + out_file)
        output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + HTMLFooter_str + HTMLEnd_str
        fsys = open(out_path + out_file, "w")
        fsys.write(output)
        fsys.close()
        return True


def replace_html_report_vars(InputStr, Title):
    sOutPut = InputStr.replace("--------PH_TITLE-------", str(Title))
    sOutPut = sOutPut.replace("--------PH_DATE-------", str(date.today()))
    return sOutPut
