#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phTaskzipper.py) - Create Zip of tasks
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
from msilib.schema import File
from tabulate import tabulate
from datetime import date
from zipfile import ZipFile

#Plumhound Modules
from lib.phLoggy import Loggy as Loggy

def ZipTasks(verbose,Processed_Results_List, OutPathFile):
    Loggy(verbose,900, "------ENTER: Task Zipper-----")
    Loggy(verbose,200, "Preparing ZipFile " + OutPathFile)
    with ZipFile(OutPathFile,"w") as NewzipFile:
        for entry in Processed_Results_List:
            filename = entry[2]
            Loggy(verbose,200, "Zip-ADD: " + filename + " Into " + OutPathFile)
            NewZipFile.write(filename)

    Loggy(verbose,110, "ZipTasks Complete: " + OutPathFile)
    Loggy(verbose,900, "------EXIT: Task Zipper-----")
    return True


