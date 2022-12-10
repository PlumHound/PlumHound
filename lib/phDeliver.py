#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound - Output Delivery and Parsing Functions(phdeliver.py)
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
import ast
import csv
from tabulate import tabulate
from datetime import datetime

#Plumhound Modules
from lib.phLoggy import Loggy as Loggy

def SenditOut(verbose,list_KeysList, Processed_Results_List, OutFormat, OutFile, OutPath, Title, HTMLHeader, HTMLFooter, HTMLCSS, jobQuery):
    Loggy(verbose,900, "------ENTER: SENDITOUT-----")
    # Quick fix if keys returned no records to properly rebuild the keys list of 0, instead of int(0)
    if isinstance(list_KeysList, int):
        list_KeysList = []
    output = ""

    if OutFormat == "CSV":
        Loggy(verbose,500, "Beginning Output CSV:" + OutPath + OutFile)
        with open(OutPath + OutFile, "w", newline="") as f:
            Loggy(verbose,500, "KeyType: " + str(type(list_KeysList)))
            Loggy(verbose,500, "KeyList: " + str((list_KeysList)))
            writer = csv.writer(f)
            ModKeyList = ast.literal_eval("[" + str(list_KeysList) + "]")
            Loggy(verbose,500, "KeyTypeMod: " + str(type(ModKeyList)))
            Loggy(verbose,500, "KeyListMod: " + str(ModKeyList))
            writer.writerows(ModKeyList)
            Loggy(verbose,500, "ResultsType: " + str(type(Processed_Results_List)))
            Loggy(verbose,999, "ResultsList: " + str(Processed_Results_List))
            writer.writerows(Processed_Results_List)
        Loggy(verbose,150, "Task " + Title + " Complete: " + OutFile)
        return True

    if OutFormat == "HTMLCSV":
        Loggy(verbose,500, "Beginning Output HTMLCSV:" + OutPath + OutFile)
        SenditOut(verbose,list_KeysList, Processed_Results_List, "HTML", OutFile + ".html", OutPath, Title, HTMLHeader, HTMLFooter, HTMLCSS, jobQuery)
        SenditOut(verbose,list_KeysList, Processed_Results_List, "CSV", OutFile + ".csv", OutPath, Title, HTMLHeader, HTMLFooter, HTMLCSS, jobQuery)
        Loggy(verbose,500, "Completed Output HTMLCSV:" + OutPath + OutFile)
        return True

    if OutFormat == "STDOUT":
        Loggy(verbose,500, "Beginning Standard Output:")
        print()
        output = tabulate(Processed_Results_List, list_KeysList, tablefmt="simple")
        print(output)
        print()
        return True

    if OutFormat == "HTML":
        Loggy(verbose,500, "Beginning Output HTML:" + OutFile)
        output = tabulate(Processed_Results_List, list_KeysList, tablefmt="html")
        outputq = "<br><table width=50%><thead><tr><th>Cypher Query</th></tr></thead><tr><td><tt>"+jobQuery+"</tt></td></tr></table>"
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

        Loggy(verbose,500, "File Writing " + OutPath + OutFile)
        output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + outputq + HTMLFooter_str + HTMLEnd_str
        fsys = open(OutPath + OutFile, "w")
        fsys.write(output)
        Loggy(verbose,150, "Task " + Title + " Complete: " + OutFile)
        Loggy(verbose,500, "File Closing " + OutPath + OutFile)
        fsys.close
        return True
    Loggy(verbose,900, "------EXIT: SENDITOUT-----")

def ReplaceHTMLReportVars(InputStr, Title):
    now=datetime.now()
    sOutPut = InputStr.replace("--------PH_TITLE-------", str(Title))
    sOutPut = sOutPut.replace("--------PH_DATE-------", str(now.strftime("%Y-%m-%d %H:%M:%S")))
    return sOutPut
