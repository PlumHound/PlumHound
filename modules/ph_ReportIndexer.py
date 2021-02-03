#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phReportIndexer.py) - Build Index of Reports (jobs)
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Python Libraries
from tabulate import tabulate
from datetime import date

# Plumhound Modules
from lib.phLoggy import loggy, log_calls


@log_calls
def ReportIndexer(verbose, Processed_Results_List, OutPathFile, HTMLHeader, HTMLFooter, HTMLCSS):
    list_KeysList = ["Title", "Count", "Further Details"]
    Title = "Full Report Details"

    loggy(100, "Beginning Output HTML:" + OutPathFile)

    for entry in Processed_Results_List:
        filename = entry[2]
        entry[2] = "<a href=\"" + filename + "\">Details</a>"

    output = str(tabulate(Processed_Results_List, list_KeysList, tablefmt="html"))
    output = output.replace("&lt;", "<")
    output = output.replace("&gt;", ">")
    output = output.replace("&quot;", '"')

    HTMLCSS_str = ""
    HTMLHeader_str = ""
    HTMLFooter_str = ""
    HTMLPre_str = "<HTML><head>"
    HTMLMId_str = "</head><Body>"
    HTMLEnd_str = "</body></html>"
    if HTMLHeader:
        with open(HTMLHeader, 'r') as header:
            HTMLHeader_str = header.read()
        HTMLHeader_str = ReplaceHTMLReportVars(HTMLHeader_str, Title)

    if HTMLFooter:
        with open(HTMLFooter, 'r') as footer:
            HTMLFooter_str = footer.read()
        HTMLFooter_str = ReplaceHTMLReportVars(HTMLFooter_str, Title)

    if HTMLCSS:
        with open(HTMLCSS, 'r') as css:
            HTMLCSS_str = "<style>\n" + css.read() + "\n</style>"

    loggy(500, "File Writing " + OutPathFile)
    output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + HTMLFooter_str + HTMLEnd_str
    fsys = open(OutPathFile, "w")
    fsys.write(output)
    fsys.close
    loggy(100, "Full index report written to " + OutPathFile)
    return True


def ReplaceHTMLReportVars(InputStr, Title):
    sOutPut = InputStr.replace("--------PH_TITLE-------", str(Title))
    sOutPut = sOutPut.replace("--------PH_DATE-------", str(date.today()))
    return sOutPut
