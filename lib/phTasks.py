#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phtasks.py) - Task Management and Execution
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
import ast
import copy
from alive_progress import alive_bar
from neo4j import GraphDatabase
from neo4j import unit_of_work

#Plumhound modules
from lib.phLoggy import Loggy as Loggy
import lib.phDeliver

#Plumhound Extensions
import modules.BlueHound
import modules.ph_ReportIndexer
import modules.ph_TaskZipper

def MakeTaskList(phArgs):
    Loggy(phArgs.verbose,900, "------ENTER: MAKETASKLIST-----")
    Loggy(phArgs.verbose,200, "Building Task List")

    tasks = []

    if phArgs.TaskFile:
        Loggy(phArgs.verbose,500, "Tasks file specified.  Reading")
        with open(phArgs.TaskFile) as f:
            tasks = f.read().splitlines()
        Loggy(phArgs.verbose,500, "TASKS: " + str(tasks))
        Loggy(phArgs.verbose,90, "Found " +str(len(tasks))+" task(s)")
        Loggy(phArgs.verbose,90, "--------------------------------------")
        Loggy(phArgs.verbose,90, "")
        Loggy(phArgs.verbose,90, "")
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
        bp=modules.BlueHound.find_busiest_path(phArgs.server, phArgs.username, phArgs.password, phArgs.BusiestPath[0], phArgs.BusiestPath[1])

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
        modules.BlueHound.getpaths(phArgs.server, phArgs.username, phArgs.password,snode,enode)

    if phArgs.easy:
        Loggy(phArgs.verbose,500, "Tasks Easy Query Specified.")
        tasks = ['["Domain Users (Limit 10)","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname LIMIT 10"]']
        Loggy(phArgs.verbose,100, "Found " +str(len(tasks))+" task(s)")
        Loggy(phArgs.verbose,100, "--------------------------------------")
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

    # Correct Path if sent as command line/not default. 
    if "//" not in Outpath:
        Outpath=phArgs.path + "//"

    jobHTMLHeader = phArgs.HTMLHeader
    jobHTMLFooter = phArgs.HTMLFooter
    jobHTMLCSS = phArgs.HTMLCSS

    task_output_list = []

    tasksuccess=0
         
    with alive_bar(len(tasks),title='\t Executing Tasks',length=50,theme='smooth',spinner=None,dual_line=True,monitor="Tasks {count} / {total} ") as tpbar:
        for job in tasks:
            tpbar()
            try:
                Loggy(phArgs.verbose,500, "Job: " + str(job))

                job_List = ast.literal_eval(job)
                jobTitle = job_List[0]
                jobOutFormat = job_List[1]
                jobOutPathFile = Outpath + job_List[2]
                jobQuery = job_List[3]

                tpbar.text("\t -> Task: " + jobTitle)

                Loggy(phArgs.verbose,200, "Starting job: " + jobTitle)

                Loggy(phArgs.verbose,500, "Job Title: " + jobTitle)
                Loggy(phArgs.verbose,500, "Job Format: " + jobOutFormat)
                Loggy(phArgs.verbose,500, "Job File: " + jobOutPathFile)
                Loggy(phArgs.verbose,500, "Job Query: " + jobQuery)

                if jobQuery == "REPORT-INDEX":
                    task_output_list_clean = copy.deepcopy(task_output_list) #copy the list and revert it after ReportIndexer
                    modules.ph_ReportIndexer.ReportIndexer(phArgs.verbose,task_output_list, jobOutPathFile, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
                    task_output_list = task_output_list_clean 
                    task_output_list.append([jobTitle, len(jobresults_processed_list), job_List[2],jobOutFormat])
                    tasksuccess += 1
                    continue

                if jobQuery == "ZIP-TASKS":
                    Loggy(phArgs.verbose,200, "task_output_list: " + str(task_output_list))
                    modules.ph_TaskZipper.ZipTasks(phArgs.verbose,task_output_list, jobOutPathFile, Outpath)
                    tasksuccess += 1
                    continue
                
                #now returns native dict containing keys
                jobkeys = get_keys(phArgs.verbose,phDriver, jobQuery)
                jobkeys_List = ast.literal_eval(str(jobkeys))

                # If keys returned 0, make an empty list
                if isinstance(jobkeys_List, int):
                    jobkeys_List = []

                #
                jobresults = execute_query(phArgs.verbose,phDriver, jobQuery)
                jobresults_processed = "[" + process_results(phArgs.verbose,jobresults) + "]"
                try:
                    jobresults_processed_list = ast.literal_eval(jobresults_processed)
                except Exception as er1:
                    Loggy(phArgs.verbose,100, "ERROR While parsing results (non-fatal but errors may exist in output.")
                    print(er1)
                    Loggy(phArgs.verbose,500, jobresults_processed)
                    jobresults_processed_list = jobresults_processed

                if jobOutFormat == "HTML" or jobOutFormat == "HTMLCSV" or jobOutFormat == "CSV":
                    task_output_list.append([jobTitle, len(jobresults_processed_list), job_List[2],jobOutFormat])

                Loggy(phArgs.verbose,500, "Exporting Job Results")
                lib.phDeliver.SenditOut(phArgs.verbose,jobkeys_List, jobresults_processed_list, jobOutFormat, jobOutPathFile, "", jobTitle, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS, jobQuery)
                tasksuccess += 1

            except Exception as er2:
                Loggy(phArgs.verbose,100, "ERROR While running job (trying next job in list).")
                print(er2)

    Loggy(phArgs.verbose,90, "")
    Loggy(phArgs.verbose,90, "Completed " + str(tasksuccess) + " of " + str(len(tasks)) + " tasks.")        
    Loggy(phArgs.verbose,90, "")   


    Loggy(phArgs.verbose,900, "------EXIT: TASKEXECUTION-----")

    if tasksuccess != (len(tasks)):
        Loggy(phArgs.verbose,100, "Completed " + str(tasksuccess) + " of " + str(len(tasks)) + " tasks (Non-Lethal errors occurred).")

    Loggy(phArgs.verbose,90, "")   

# Setup Query
@unit_of_work(timeout=300)
def execute_query(verbose, phDriver, query, enabled=True):
    Loggy(verbose,900, "------ENTER: EXECUTE_QUERY-----")
    try:
        with phDriver.session() as session:
            Loggy(verbose,500, "Running Query")
            results = session.run(query)
            #results return a <class 'neo4j._sync.work.result.Result'>
            #https://neo4j.com/docs/api/python-driver/current/api.html#result
            #I have tried getting the number of records in the object, but its a bit tricky, all functions doing it in one step ive tired have been deprecated and removed in the new driver
            #even tried making a summary object before getting the real data:
            #https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.ResultSummary
            #results = session.run(query)
            #summary = results.consume()
            #results = session.run(query)
            #count = summary.counters.nodes_created()
            #data = results.fetch(count)
            #Bloodhounds javascript is using recursion, id say its the way to go
            data = results.fetch(999999999999)
            if check_records(verbose, phDriver, query):
                Loggy(verbose,500, "Identified " + str(len(data)) + " Results")
            else:
                Loggy(verbose,200, "Job result: No records found")
        Loggy(verbose,900, "------EXIT: EXECUTE_QUERY-----")
    except Exception as er3:
        Loggy(verbose,200,"Error occured in execute_query: ")
        print(er3)
    return data


# Grab Keys for Cypher Query
@unit_of_work(timeout=300)
def get_keys(verbose,phDriver, query, enabled=True):
    Loggy(verbose,900, "------ENTER: get_keys-----")
    try:
        Loggy(verbose,500, "get_keys Query: " + str(query))
        with phDriver.session() as session:
            results = session.run(query)
            keys = results.keys()
            if check_records(verbose, phDriver, query):
                keys = results.keys()
                Loggy(verbose,500, "Identified " + str(len(keys)) + " Results")
                Loggy(verbose,500, "Keys Found")
            else:
                Loggy(verbose,200, "No Keys found")
                keys = 0
        Loggy(verbose,500, "Key enumeration complete")
        Loggy(verbose,900, "------EXIT: get_keys-----")
    except Exception as er4:
        Loggy(verbose,200,"Error occured in get_keys: ")
        print(er4)
    return keys


def check_records(verbose, phDriver, query):
    Loggy(verbose,900, "------ENTER: check_records-----")
    try:
        with phDriver.session() as session:
            results = session.run(query)
            first = results.peek()
            if first:
                Loggy(verbose,500, "Found Records")
            else:
                Loggy(verbose,200, "No Records Found")
            Loggy(verbose,900, "------EXIT: check_records-----")
    except Exception as er5:
        Loggy(verbose,200,"Error occured in check_records: ")
        print(er5)
    return first


def process_results(verbose,results):
    Loggy(verbose,900, "------ENTER: process_results-----")
    BigTable = ""
    for record in results:
        try:
            BigTable = BigTable + str(record.values()) + ","
        except Exception as er6:
            Loggy(verbose,200, "Washing records failed. Error on record")
            print(er6)
    Loggy(verbose,900, "------EXIT: process_results-----")
    return BigTable
