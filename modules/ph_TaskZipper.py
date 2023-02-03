#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phTaskzipper.py) - Create Zip of tasks
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
from datetime import date
from zipfile import ZipFile

#Plumhound Modules
from lib.phLoggy import Loggy as Loggy

def ZipTasks(verbose,Processed_Results_List, OutPathFile, Outpath):
    Loggy(verbose,900, "------ENTER: Task Zipper-----")
    Loggy(verbose,200, "Preparing ZipFile " + OutPathFile)
    with ZipFile(OutPathFile,"w") as NewZipFile:
        for entry in Processed_Results_List:
            filename=Outpath + entry[2]
            if entry[3] == "HTMLCSV":
                Loggy(verbose,200, "Zip-ADD: " + filename + ".csv Into " + OutPathFile)
                NewZipFile.write(filename + ".csv")
                Loggy(verbose,200, "Zip-ADD: " + filename + ".html Into " + OutPathFile)
                NewZipFile.write(filename + ".html")
            else:
                Loggy(verbose,200, "Zip-ADD: " + filename + " Into " + OutPathFile)
                NewZipFile.write(filename)

    Loggy(verbose,99, "Completed Reports Archive: " + OutPathFile)
    Loggy(verbose,900, "------EXIT: Task Zipper-----")
    return True


