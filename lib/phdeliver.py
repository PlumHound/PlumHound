#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
import sys
import ast
import csv
from tabulate import tabulate
from datetime import date

#Plumhound Modules
from lib.phLoggy import Loggy as Loggy


def SenditOut(list_KeysList, Processed_Results_List, OutFormat, OutFile, OutPath, Title, HTMLHeader, HTMLFooter, HTMLCSS):
    Loggy(900, "------ENTER: SENDITOUT-----")
    # Quick fix if keys returned no records to properly rebuild the keys list of 0, instead of int(0)
    if isinstance(list_KeysList, int):
        list_KeysList = []
    output = ""

    if OutFormat == "CSV":
        Loggy(100, "Beginning Output CSV:" + OutPath + OutFile)
        with open(OutPath + OutFile, "w", newline="") as f:
            Loggy(500, "KeyType: " + str(type(list_KeysList)))
            Loggy(500, "KeyList: " + str((list_KeysList)))
            writer = csv.writer(f)
            ModKeyList = ast.literal_eval("[" + str(list_KeysList) + "]")
            Loggy(500, "KeyTypeMod: " + str(type(ModKeyList)))
            Loggy(500, "KeyListMod: " + str(ModKeyList))
            writer.writerows(ModKeyList)
            Loggy(500, "ResultsType: " + str(type(Processed_Results_List)))
            Loggy(999, "ResultsList: " + str(Processed_Results_List))
            writer.writerows(Processed_Results_List)
        return True

    if OutFormat == "STDOUT":
        print()
        output = tabulate(Processed_Results_List, list_KeysList, tablefmt="simple")
        print(output)
        return True

    if OutFormat == "HTML":
        Loggy(100, "Beginning Output HTML:" + OutFile)

        output = tabulate(Processed_Results_List, list_KeysList, tablefmt="html")
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

        Loggy(500, "File Writing " + OutPath + OutFile)
        output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + HTMLFooter_str + HTMLEnd_str
        fsys = open(OutPath + OutFile, "w")
        fsys.write(output)
        fsys.close
        return True
    Loggy(900, "------EXIT: SENDITOUT-----")


def FullSenditOut(Processed_Results_List, OutPath, HTMLHeader, HTMLFooter, HTMLCSS):
    Loggy(900, "------ENTER: FULLSENDITOUT-----")

    list_KeysList = ["Title", "Count", "Further Details"]
    OutFile = "Report.html"
    Title = "Full Report Details"

    Loggy(100, "Beginning Output HTML:" + OutFile)

    for entry in Processed_Results_List:
        filename = entry[2]
        entry[2] = "<a href=\"" + filename + "\">Details</a>"

    output = str(tabulate(Processed_Results_List, list_KeysList, tablefmt="html"))
    output = output.replace("&lt;","<")
    output = output.replace("&gt;",">")
    output = output.replace("&quot;",'"')

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

    Loggy(500, "File Writing " + OutPath + OutFile)
    output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + HTMLFooter_str + HTMLEnd_str
    fsys = open(OutPath + OutFile, "w")
    fsys.write(output)
    fsys.close
    Loggy(100, "Full report written to Report.html")
    return True
    Loggy(900, "------EXIT: FULLSENDITOUT-----")


def ReplaceHTMLReportVars(InputStr, Title):
    sOutPut = InputStr.replace("--------PH_TITLE-------", str(Title))
    sOutPut = sOutPut.replace("--------PH_DATE-------", str(date.today()))
    return sOutPut