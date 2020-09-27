#!/usr/bin/env python
# -*- coding: utf8 -*-

# PlumHound v01.070a

# PlumHound https://github.com/DefensiveOrigins/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHound Wrapper for Purple Teams
# ToolDropped May 13th 2020 as Proof of Concept Code - Black Hills Information Security #BHInfoSecurity #DefensiveOGs

# GNU GPL 3.0

# imports
import argparse
import sys
import ast
import csv
from neo4j import GraphDatabase
from tabulate import tabulate
from datetime import date
from BlueHound import *


def CheckPython():
    if sys.version_info < (3, 0, 0):
        print(__file__ + ' requires Python 3, while Python ' + str(sys.version[0] + ' was detected. Terminating. '))
        sys.exit(1)


# ArgumentSetups
parser = argparse.ArgumentParser(description="BloodHound Wrapper for Blue/Purple Teams; v01.070a", add_help=True, epilog="For more information see https://plumhound.DefensiveOrigins.com")
pgroupc = parser.add_argument_group('DATABASE')
pgroupc.add_argument("-s", "--server", type=str, help="Neo4J Server", default="bolt://localhost:7687")
pgroupc.add_argument("-u", "--username", default="neo4j", type=str, help="Neo4J Database Useranme")
pgroupc.add_argument("-p", "--password", default="neo4jj", type=str, help="Neo4J Database Password")
pgroupc.add_argument("--UseEnc", default=False, dest="UseEnc", help="Use encryption when connecting.", action='store_true')

pgroupx = parser.add_mutually_exclusive_group(required="True")
pgroupx.add_argument("--easy", help="Test Database Connection, Returns Domain Users to stdout", action='store_true')
pgroupx.add_argument("-x", "--TaskFile", dest="TaskFile", type=str, help="Specify a PlumHound TaskList File")
pgroupx.add_argument("-c," "--QuerySingle", dest="querysingle", type=str, help="Specify a Single cypher Query")
pgroupx.add_argument("-ap," "--AnalyzePath", dest="AnalyzePath", nargs='+', default="User", type=str, help="Analyze 'Attack Paths' between two nodes and find which path needs to be remediated to brake the path.")

pgroupo = parser.add_argument_group('OUTPUT', "Output Options (For single cypher queries only. --These options are ignored when -x or --easy is specified.")
pgroupo.add_argument("-t", "--title", dest="title", default="Adhoc Query", type=str, help="Report Title for Single Query [HTML,CSV,Latex]")
pgroupo.add_argument("--of", "--OutFile", dest="OutFile", default="PlumHoundReport", type=str, help="Specify a Single Cypher Query")
pgroupo.add_argument("--op", "--OutPath", dest="path", default="reports//", type=str, help="Specify an Output Path for Reports")
pgroupo.add_argument("--ox", "--OutFormat", dest="OutFormat", default="stdout", type=str, help="Specify the type of output", choices=['stdout', 'HTML', 'CSV'])

pgrouph = parser.add_argument_group('HTML', "Options for HTML Output (For single queries or TaskLists")
pgrouph.add_argument("--HTMLHeader", dest="HTMLHeader", type=str, default="template//head.html", help="HTML Header (file) of Report")
pgrouph.add_argument("--HTMLFooter", dest="HTMLFooter", type=str, default="template//tail.html", help="HTML Footer (file) of Report")
pgrouph.add_argument("--HTMLCSS", dest="HTMLCSS", type=str, default="template//html.css", help="Specify a CSS template for HTML Output")

pgroupv = parser.add_argument_group('VERBOSE' "Set verbosity")
pgroupv.add_argument("-v", "--verbose", type=int, default="100", help="Verbosity 0-1000, 0 = quiet")
args = parser.parse_args()


# Loggy Function for lazy debugging
def Loggy(level, notice):
    if level <= args.verbose:
        if level <= 100:
            print("[*]" + notice)
        elif level < 500:
            print("[!]" + notice)
        else:
            print("[*]" + notice)


# Setup Database Connection
def setup_database_conn(server, username, password):
    Loggy(900, "------ENTER: SETUP_DATABASE_CONN-----")
    Loggy(200, "[!] Attempting to connect to your Neo4j project using {}:{} @ {} {}.".format(username, password, server, "[ENCRYPTED]" if args.UseEnc else "[UNECNCRYPTED]"))
    try:
        if args.UseEnc:
            Loggy(200, " Using Neo4j encryption")
            driver_connection = GraphDatabase.driver(server, auth=(username, password), encrypted=True)
        else:
            Loggy(200, " Not using Neo4j encryption")
            driver_connection = GraphDatabase.driver(server, auth=(username, password), encrypted=False)
        Loggy(200, "[+] Success!")
        return driver_connection
    except Exception:
        Loggy(100, "There was a problem. Check username, password, and server parameters.")
        Loggy(100, "[X] Database connection failed!")
        exit()
    Loggy(900, "------EXIT: SETUP_DATABASE_CONN-----")


def MakeTaskList():
    Loggy(900, "------ENTER: MAKETASKLIST-----")
    Loggy(100, "Building Task List")

    tasks = []

    if args.TaskFile:
        Loggy(500, "Tasks file specified.  Reading")
        with open(args.TaskFile) as f:
            tasks = f.read().splitlines()
        Loggy(500, "TASKS: " + str(tasks))
        return tasks

    if args.querysingle:
        Loggy(500, "Tasks Single Query Specified. Reading")
        Loggy(500, "Tasks-Title:" + args.title)
        Loggy(500, "Tasks-OutFormat:" + args.OutFormat)
        Loggy(500, "Tasks-OutPath:" + args.path)
        Loggy(500, "Tasks-QuerySingle:" + args.querysingle)

        task_str = "[\"" + args.title + "\",\"" + args.OutFormat + "\",\"" + args.OutFile + "\",\"" + args.querysingle + "\"]"
        Loggy(500, "Task_str:  " + task_str)
        tasks = [task_str]
        return tasks

    if args.AnalyzePath:
        if args.AnalyzePath[0].upper() == "USER":
            snode="User"
            enode=""
        elif args.AnalyzePath[0].upper() == "GROUP":
            snode="Group"
            enode=""
        elif args.AnalyzePath[0].upper() == "COMPUTER":
            snode="Computer"
            enode=""
        elif args.AnalyzePath[0].upper() == "OU":
            snode="OU"
            enode=""
        elif args.AnalyzePath[0].upper() == "GPO":
            snode="GPO"
            enode=""
        else:
            snode=(args.AnalyzePath[0]).upper()
            enode=(args.AnalyzePath[1]).upper()
        bh_getpaths(snode,enode)

    if args.easy:
        Loggy(500, "Tasks Easy Query Specified.")
        tasks = ['["Domain Users","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname"]']
        return tasks

    Loggy(100, "Tasks Generation Completed\nTasks: " + str(tasks))
    Loggy(900, "------EXIT: MAKETASKLIST-----")
    return tasks


# Start Executions
def TaskExecution(tasks, Outpath, HTMLHeader, HTMLFooter, HTMLCSS):
    Loggy(900, "------ENTER: TASKEXECUTION-----")
    Loggy(500, "Begin Task Executions")
    Loggy(500, "TASKS:/n" + str(tasks))

    jobHTMLHeader = HTMLHeader
    jobHTMLFooter = HTMLFooter
    jobHTMLCSS = HTMLCSS

    for job in tasks:
        try:
            Loggy(200, "Starting job")
            Loggy(500, "Job: " + str(job))

            job_List = ast.literal_eval(job)
            jobTitle = job_List[0]
            jobOutFormat = job_List[1]
            jobOutPathFile = Outpath + job_List[2]
            jobQuery = job_List[3]

            Loggy(500, "Job Title: " + jobTitle)
            Loggy(500, "Job Format: " + jobOutFormat)
            Loggy(500, "Job File: " + jobOutPathFile)
            Loggy(500, "Job Query: " + jobQuery)

            jobkeys = GetKeys(newdriver, jobQuery)
            jobkeys_List = ast.literal_eval(str(jobkeys))
            # Quick fix if keys returned no record sto properly rebuild the keys list as 0 records, instead of int(0)
            if isinstance(jobkeys_List, int):
                jobkeys_List = []

            jobresults = execute_query(newdriver, jobQuery)
            jobresults_processed = "[" + processresults(jobresults) + "]"

            try:
                jobresults_processed_list = ast.literal_eval(jobresults_processed)
            except Exception:
                Loggy(200, "ERROR While parsing results (non-fatal but errors may exist in output.")
                Loggy(500, jobresults_processed)
                jobresults_processed_list = jobresults_processed

            Loggy(500, "Calling delivery service")
            SenditOut(jobkeys_List, jobresults_processed_list, jobOutFormat, jobOutPathFile, "", jobTitle, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
        except Exception:
            Loggy(200, "ERROR While trying to parse jobs (move along).")
    Loggy(900, "------EXIT: TASKEXECUTION-----")


# Setup Query
def execute_query(driver, query, enabled=True):
    Loggy(900, "------ENTER: EXECUTE_QUERY-----")
    Loggy(500, "Executing things")

    with driver.session() as session:
        Loggy(500, "Running Query")
        results = session.run(query)
        if check_records(results):
            count = results.detach()
            Loggy(500, "Identified " + str(count) + " Results")
        else:
            Loggy(200, "Shoot, nothing interesting was found")
    Loggy(900, "------EXIT: EXECUTE_QUERY-----")
    return results


# Grab Keys for Cypher Query
def GetKeys(driver, query, enabled=True):
    Loggy(900, "------ENTER: GETKEYS-----")
    Loggy(500, "Locating Keys")
    Loggy(500, "GetKeys Query:" + str(query))
    with driver.session() as session:
        results = session.run(query)
        if check_records(results):
            keys = results.keys()
            Loggy(500, "Identified Keys: " + str(keys))
        else:
            Loggy(200, "No Keys found, this won't go well")
            keys = 0
    Loggy(500, "Key enumeration complete")
    Loggy(900, "------EXIT: GETKEYS-----")

    return keys


def check_records(results):
    Loggy(900, "------ENTER: CHECK_RECORDS-----")
    if results.peek():
        Loggy(500, "Peeking at things")
        return True
    else:
        Loggy(200, "Nothing found to peek at")
        return False
    Loggy(900, "------EXIT: CHECK_RECORDS-----")


def processresults(results):
    Loggy(900, "------ENTER: PROCESSRESULTS-----")
    Loggy(500, "Results need washed")
    BigTable = ""
    for record in results:
        try:
            BigTable = BigTable + str(record.values()) + ","
        except Exception:
            Loggy(200, "Washing records failed. Error on record")
    Loggy(900, "------EXIT: PROCESSRESULTS-----")
    return BigTable


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


def ReplaceHTMLReportVars(InputStr, Title):
    sOutPut = InputStr.replace("--------PH_TITLE-------", str(Title))
    sOutPut = sOutPut.replace("--------PH_DATE-------", str(date.today()))
    return sOutPut


# Check for Python3 environment.
CheckPython()

# Setup Driver
newdriver = setup_database_conn(args.server, args.username, args.password)

# Read Task List
TaskList = MakeTaskList()

# Start Task List
TaskExecution(TaskList, args.path, args.HTMLHeader, args.HTMLFooter, args.HTMLCSS)

# Close out neo4j connection
newdriver.close

# END
