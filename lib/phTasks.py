#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phtasks.py) - Task Management and Execution
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
import sys
import ast
from tabulate import tabulate
from datetime import date
from neo4j import GraphDatabase

#Plumhound modules
from lib.phLoggy import Loggy as Loggy
import lib.phDeliver

#Plumhound Extensions
from modules.BlueHound import *


def MakeTaskList(phArgs):
    Loggy(phArgs.verbose,900, "------ENTER: MAKETASKLIST-----")
    Loggy(phArgs.verbose,100, "Building Task List")

    tasks = []

    if phArgs.TaskFile:
        Loggy(phArgs.verbose,500, "Tasks file specified.  Reading")
        with open(phArgs.TaskFile) as f:
            tasks = f.read().splitlines()
        Loggy(phArgs.verbose,500, "TASKS: " + str(tasks))
        return tasks

    if phArgs.QuerySingle:
        Loggy(phArgs.verbose,500, "Tasks Single Query Specified. Reading")
        Loggy(phArgs.verbose,500, "Tasks-Title:" + phArgs.title)
        Loggy(phArgs.verbose,500, "Tasks-OutFormat:" + phArgs.OutFormat)
        Loggy(phArgs.verbose,500, "Tasks-OutPath:" + phArgs.path)
        Loggy(phArgs.verbose,500, "Tasks-QuerySingle:" + phArgs.QuerySingle)

        task_str = "[\"" + phArgs.title + "\",\"" + phArgs.OutFormat + "\",\"" + phArgs.OutFile + "\",\"" + phArgs.QuerySingle + "\"]"
        Loggy(phArgs.verbose,500, "Task_str:  " + task_str)
        tasks = [task_str]
        return tasks

    if phArgs.BusiestPath:
        # Find and print on screen the X Attack Paths that give the most users a path to DA
        bp=find_busiest_path(phArgs.server, phArgs.username, phArgs.password, phArgs.BusiestPath[0], phArgs.BusiestPath[1])

    if phArgs.AnalyzePath:
        if phArgs.AnalyzePath[0].upper() == "USER":
            snode="User"
            enode=""
        elif phArgs.AnalyzePath[0].upper() == "GROUP":
            snode="Group"
            enode=""
        elif phArgs.AnalyzePath[0].upper() == "COMPUTER":
            snode="Computer"
            enode=""
        else:
            snode=(phArgs.AnalyzePath[0]).upper()
            enode=(phArgs.AnalyzePath[1]).upper()
        BueHound.getpaths(phArgs.server, phArgs.username, phArgs.password,snode,enode)

    if phArgs.easy:
        Loggy(phArgs.verbose,500, "Tasks Easy Query Specified.")
        tasks = ['["Domain Users","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname"]']
        return tasks

    Loggy(phArgs.verbose,100, "Tasks Generation Completed\nTasks: " + str(tasks))
    Loggy(phArgs.verbose,900, "------EXIT: MAKETASKLIST-----")
    return tasks


# Execute Tasks
def TaskExecution(tasks, phDriver, phArgs):

    Loggy(phArgs.verbose,900, "------ENTER: TASKEXECUTION-----")
    Loggy(phArgs.verbose,500, "Begin Task Executions")
    Loggy(phArgs.verbose,500, "TASKS:" + str(tasks))

    Outpath=phArgs.path
    jobHTMLHeader = phArgs.HTMLHeader
    jobHTMLFooter = phArgs.HTMLFooter
    jobHTMLCSS = phArgs.HTMLCSS

    task_output_list = []

    for job in tasks:
        try:

            Loggy(phArgs.verbose,500, "Job: " + str(job))

            job_List = ast.literal_eval(job)
            jobTitle = job_List[0]
            jobOutFormat = job_List[1]
            jobOutPathFile = Outpath + job_List[2]
            jobQuery = job_List[3]

            Loggy(phArgs.verbose,200, "Starting job: " + jobTitle)

            Loggy(phArgs.verbose,500, "Job Title: " + jobTitle)
            Loggy(phArgs.verbose,500, "Job Format: " + jobOutFormat)
            Loggy(phArgs.verbose,500, "Job File: " + jobOutPathFile)
            Loggy(phArgs.verbose,500, "Job Query: " + jobQuery)

            jobkeys = GetKeys(phArgs.verbose,phDriver, jobQuery)
            jobkeys_List = ast.literal_eval(str(jobkeys))
            
            # If keys returned 0, make an empty list
            if isinstance(jobkeys_List, int):
                jobkeys_List = []
            
            jobresults = execute_query(phArgs.verbose,phDriver, jobQuery)
            jobresults_processed = "[" + processresults(phArgs.verbose,jobresults) + "]"
            try:
                jobresults_processed_list = ast.literal_eval(jobresults_processed)
            except Exception:
                Loggy(phArgs.verbose,200, "ERROR While parsing results (non-fatal but errors may exist in output.")
                Loggy(phArgs.verbose,500, jobresults_processed)
                jobresults_processed_list = jobresults_processed

            if jobOutFormat == "HTML":
                task_output_list.append([jobTitle, len(jobresults_processed_list), job_List[2]])

            Loggy(phArgs.verbose,500, "Calling delivery service")
            lib.phDeliver.SenditOut(phArgs.verbose,jobkeys_List, jobresults_processed_list, jobOutFormat, jobOutPathFile, "", jobTitle, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
        except Exception:
            Loggy(phArgs.verbose,200, "ERROR While running job (trying next job in list).")

    Loggy(phArgs.verbose,900, "------EXIT: TASKEXECUTION-----")

    if len(task_output_list) != 0:
        Loggy(phArgs.verbose,200, "Found:" + str(len(task_output_list)) +" jobs to export")
        lib.phDeliver.FullSenditOut(phArgs.verbose,task_output_list, Outpath, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
    else:
        Loggy(phArgs.verbose,200, "ERROR - No reports found to export.")

# Setup Query
def execute_query(verbose,phDriver, query, enabled=True):
    Loggy(verbose,900, "------ENTER: EXECUTE_QUERY-----")
    Loggy(verbose,500, "Executing things")

    with phDriver.session() as session:
        Loggy(verbose,500, "Running Query")
        results = session.run(query)
        if check_records(verbose,results):
            count = results.detach()
            Loggy(verbose,500, "Identified " + str(count) + " Results")
        else:
            Loggy(verbose,200, "Job result: No records found")
    Loggy(verbose,900, "------EXIT: EXECUTE_QUERY-----")
    return results


# Grab Keys for Cypher Query
def GetKeys(verbose,phDriver, query, enabled=True):
    Loggy(verbose,900, "------ENTER: GETKEYS-----")
    Loggy(verbose,500, "Locating Keys")
    Loggy(verbose,500, "GetKeys Query:" + str(query))
    with phDriver.session() as session:
        results = session.run(query)
        if check_records(verbose,results):
            keys = results.keys()
            Loggy(verbose,500, "Keys Found")
        else:
            Loggy(verbose,200, "No Keys found")
            keys = 0
    Loggy(verbose,500, "Key enumeration complete")
    Loggy(verbose,900, "------EXIT: GETKEYS-----")
    return keys


def check_records(verbose,results):
    Loggy(verbose,900, "------ENTER: CHECK_RECORDS-----")
    if results.peek():
        Loggy(verbose,500, "Found Records")
    else:
        Loggy(verbose,200, "No Records Found")
    Loggy(verbose,900, "------EXIT: CHECK_RECORDS-----")
    return results.peek()


def processresults(verbose,results):
    Loggy(verbose,900, "------ENTER: PROCESSRESULTS-----")
    Loggy(verbose,500, "Results need washed")
    BigTable = ""
    for record in results:
        try:
            BigTable = BigTable + str(record.values()) + ","
        except Exception:
            Loggy(verbose,200, "Washing records failed. Error on record")
    Loggy(verbose,900, "------EXIT: PROCESSRESULTS-----")
    return BigTable
