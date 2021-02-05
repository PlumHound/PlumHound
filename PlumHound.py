#!/usr/bin/env python
# -*- coding: utf8 -*-

# PlumHound https://github.com/PlumHound/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHoundAD Wrapper for Purple Teams | https://github.com/BloodHoundAD/BloodHound

# GNU GPL 3.0

# Import PlumHound libraries
import lib.phCheckPython
import lib.phCLImanagement
import lib.phTasks
import lib.phDatabase

# Check for Python3 environment.  If not executing in Python3, exit nicely.
lib.phCheckPython.CheckPython()

# Commandline Arguments (ArgParse) configuration
phArgs = lib.phCLImanagement.parse_arguments()

# Generate TaskList (jobs)
phTaskList = lib.phTasks.make_task_list(phArgs)

# Setup Driver (excluding BlueHound)
phDriver = lib.phDatabase.setup_database_conn(phArgs)

# Execute Jobs in Task List
results = lib.phTasks.execute_tasks(phTaskList, phDriver, phArgs)

if phArgs.explore:
    from interface.backend.phBackend import start

    start(phArgs.port, results)

# Close the neoj4 connection.
lib.phDatabase.close_database_con(phArgs, phDriver)
