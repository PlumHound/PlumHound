#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phtasks.py) - Task Management and Execution
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Python Libraries
import ast

# Plumhound modules
from lib.phLoggy import loggy, set_log_hurdle, log_calls
import lib.phDeliver

# Plumhound Extensions
import modules.BlueHound
import modules.ph_ReportIndexer


@log_calls
def MakeTaskList(phArgs):
    set_log_hurdle(phArgs.verbose)

    loggy(100, "Building Task List")

    tasks = []

    if phArgs.TaskFile:
        loggy(500, "Tasks file specified.  Reading")
        with open(phArgs.TaskFile) as f:
            tasks = f.read().splitlines()
        loggy(500, "TASKS: " + str(tasks))
        return tasks

    if phArgs.QuerySingle:
        loggy(500, "Tasks Single Query Specified. Reading")
        loggy(500, "Tasks-Title:" + phArgs.title)
        loggy(500, "Tasks-OutFormat:" + phArgs.OutFormat)
        loggy(500, "Tasks-OutPath:" + phArgs.path)
        loggy(500, "Tasks-QuerySingle:" + phArgs.QuerySingle)

        task_str = "[\"" + phArgs.title + "\",\"" + phArgs.OutFormat + "\",\"" + phArgs.OutFile + "\",\"" + phArgs.QuerySingle + "\"]"
        loggy(500, "Task_str:  " + task_str)
        tasks = [task_str]
        return tasks

    if phArgs.BusiestPath:
        # Find and print on screen the X Attack Paths that give the most users a path to DA
        modules.BlueHound.find_busiest_path(phArgs.server, phArgs.username, phArgs.password, phArgs.BusiestPath[0], phArgs.BusiestPath[1])

    if phArgs.AnalyzePath:
        if phArgs.AnalyzePath[0].upper() == "USER":
            snode = "User"
            enode = ""
        elif phArgs.AnalyzePath[0].upper() == "GROUP":
            snode = "Group"
            enode = ""
        elif phArgs.AnalyzePath[0].upper() == "COMPUTER":
            snode = "Computer"
            enode = ""
        else:
            snode = (phArgs.AnalyzePath[0]).upper()
            enode = (phArgs.AnalyzePath[1]).upper()
        modules.BlueHound.getpaths(phArgs.server, phArgs.username, phArgs.password, snode, enode)

    if phArgs.easy:
        loggy(500, "Tasks Easy Query Specified.")
        tasks = ['["Domain Users","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname"]']
        return tasks

    loggy(100, "Tasks Generation Completed\nTasks: " + str(tasks))
    return tasks


# Execute Tasks
@log_calls
def TaskExecution(tasks, phDriver, phArgs):
    loggy(500, "Begin Task Executions")
    loggy(500, "TASKS:" + str(tasks))

    Outpath = phArgs.path
    jobHTMLHeader = phArgs.HTMLHeader
    jobHTMLFooter = phArgs.HTMLFooter
    jobHTMLCSS = phArgs.HTMLCSS

    task_output_list = []

    for job in tasks:
        try:

            loggy(500, "Job: " + str(job))

            job_List = ast.literal_eval(job)
            jobTitle = job_List[0]
            jobOutFormat = job_List[1]
            jobOutPathFile = Outpath + job_List[2]
            jobQuery = job_List[3]

            loggy(200, "Starting job: " + jobTitle)

            loggy(500, "Job Title: " + jobTitle)
            loggy(500, "Job Format: " + jobOutFormat)
            loggy(500, "Job File: " + jobOutPathFile)
            loggy(500, "Job Query: " + jobQuery)

            if jobQuery == "REPORT-INDEX":
                modules.ph_ReportIndexer.ReportIndexer(phArgs.verbose, task_output_list, jobOutPathFile, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
                continue
            
            jobresults, jobkeys = execute_query(phArgs.verbose, phDriver, jobQuery)
            # jobresults_processed = "[" + processresults(phArgs.verbose,jobresults) + "]"
            # print('a',jobresults_processed)
            # try:
            #     jobresults_processed_list = ast.literal_eval(jobresults_processed)
            # except Exception:
            #     loggy(200, "ERROR While parsing results (non-fatal but errors may exist in output.")
            #     loggy(500, jobresults_processed)
            #     jobresults_processed_list = jobresults_processed

            if jobOutFormat == "HTML":
                task_output_list.append([jobTitle, len(jobresults), job_List[2]])

            loggy(500, "Exporting Job Resultes")
            lib.phDeliver.send_it_out(phArgs.verbose, jobkeys, jobresults, jobOutFormat, jobOutPathFile, "", jobTitle, jobHTMLHeader, jobHTMLFooter, jobHTMLCSS)
        except Exception as e:
            raise e
            loggy(200, "ERROR While running job (trying next job in list).")

    if len(task_output_list) != 0:
        loggy(200, "Jobs:" + str(len(task_output_list)) + " jobs completed")
    else:
        loggy(200, "ERROR - No reports found to export.")


# Setup Query
@log_calls
def execute_query(verbose, phDriver, query, enabled=True) -> ([dict], [str]):
    loggy(500, "Executing things")

    with phDriver.session() as session:
        loggy(500, "Running Query")
        results = session.run(query)
        data = results.data()
        keys = results.data()
        if count := len(data) > 0:
            loggy(500, "Identified " + str(count) + " Results")
        else:
            loggy(200, "Job result: No records found")
    return (data, keys)
