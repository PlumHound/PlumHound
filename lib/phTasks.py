#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phtasks.py) - Task Management and Execution
# https://github.com/PlumHound/PlumHound
# License GNU GPL3

# Python Libraries
import json

# Plumhound modules
from lib.phLoggy import loggy, set_log_hurdle, log_calls
import lib.phDeliver

# Plumhound Extensions
import modules.BlueHound


@log_calls
def make_task_list(phArgs):
    set_log_hurdle(phArgs.verbose)

    loggy(100, "Building Task List")

    if phArgs.TaskFile:
        loggy(500, "Tasks file specified.  Reading")
        with open(phArgs.TaskFile) as f:
            tasks = json.loads(''.join(f.readlines()))
        loggy(500, f"FOUND {len(tasks['tasks'])} TASKS")
        return tasks

    if phArgs.QuerySingle:
        loggy(500, "Tasks Single Query Specified. Reading")
        loggy(500, "Tasks-Title:" + phArgs.title)
        loggy(500, "Tasks-OutFormat:" + phArgs.OutFormat)
        loggy(500, "Tasks-OutPath:" + phArgs.path)
        loggy(500, "Tasks-QuerySingle:" + phArgs.QuerySingle)

        task = {
            'name': 'Single Query',
            'type': 'query',
            'query': phArgs.QuerySingle,
            'format': phArgs.OutFormat,
            'path': phArgs.OutFile
        }
        tasks = {
            'name': phArgs.title,
            'tasks': [task]
        }
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
        modules.BlueHound.get_paths(phArgs.server, phArgs.username, phArgs.password, snode, enode)

    if phArgs.easy:
        loggy(500, "Tasks Easy Query Specified.")
        tasks = ['["Domain Users","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname"]']
        return tasks

    loggy(100, "Tasks Generation Completed\nTasks: " + str(tasks))
    return tasks


# Execute Tasks
@log_calls
def execute_tasks(tasks, phDriver, phArgs):
    loggy(500, "Begin Task Executions")
    loggy(500, f"{len(tasks['tasks'])} TASKS")

    outpath = phArgs.path

    task_output_list = [execute_task(task, phDriver, phArgs) for task in tasks['tasks']]

    if len(task_output_list) != 0:
        loggy(200, "Jobs:" + str(len(task_output_list)) + " jobs completed")
    else:
        loggy(200, "Error: There were no tasks to complete?")
        return

    loggy(500, "Exporting Job Results")

    for result in task_output_list:
        lib.phDeliver.send_it_out(phArgs.verbose, result['keys'], result['results'], result['format'], result['path'], outpath, result['title'])

    return task_output_list


def execute_task(task: dict, driver, args):
    try:
        loggy(500, "Job: " + str(task))

        job_title = task.get('title', 'Task')
        job_out_format = task.get('format', 'stdout')
        job_out_path_file = task.get('path', 'reports')
        job_type = task.get('type')

        loggy(200, "Starting job: " + job_title)

        loggy(500, "Job Title: " + job_title)
        loggy(500, "Job Format: " + job_out_format)
        if job_out_format != 'stdout':
            loggy(500, "Job Out File: " + job_out_path_file)
        loggy(500, "Job Type: " + job_type)

        if job_type == 'query':
            job_query = task['query']
            if job_query is None:
                raise Exception('query tasks should have a query parameter')
            loggy(500, "Job Query: " + job_query)
            jobresults, jobkeys = execute_query(args.verbose, driver, job_query)
        elif job_type == 'analyze_path':
            start = task.get('start')
            end = task.get('end', '')
            if start is None:
                raise Exception('analyze_path tasks should have a start parameter')
            else:
                start = start.upper()
            if start == "USER":
                snode = "User"
                enode = ""
            elif start == "GROUP":
                snode = "Group"
                enode = ""
            elif start == "COMPUTER":
                snode = "Computer"
                enode = ""
            else:
                snode = start.upper()
                enode = end.upper()
            jobresults = modules.BlueHound.get_paths(args.server, args.username, args.password, snode, enode)
            jobkeys = []  # temporary
            print(jobresults)
        elif job_type == 'busiest_path':
            method = task.get('method', 'short')
            jobresults = modules.BlueHound.find_busiest_path(args.server, args.username, args.password, method)
            jobkeys = []  # temporary

        return {
            'title': job_title,
            'results': jobresults,
            'keys': jobkeys,
            'format': job_out_format,
            'path': job_out_path_file
        }
    except Exception as e:
        raise e
        loggy(200, "ERROR While running job (trying next job in list).")


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
