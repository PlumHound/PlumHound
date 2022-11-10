#!/usr/bin/env python
# -*- coding: utf8 -*-

# PlumHound https://github.com/PlumHound/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHoundAD Wrapper for Purple Teams | https://github.com/BloodHoundAD/BloodHound

# GNU GPL 3.0

#Import PlumHound libraries
import lib.phCheckPython 
import lib.phCLImanagement
import lib.phNotifyArgs
import lib.phTasks
import lib.phDatabase

# Check for Python3 environment.  If not executing in Python3, exit nicely.
lib.phCheckPython.CheckPython()

# Commandline Arguments (ArgParse) configuration
phArgs = lib.phCLImanagement.SetupArguments()
Lib.NotifyArgs.NotifyArgs(phArgs)

# Generate TaskList (jobs)
phTaskList = lib.phTasks.MakeTaskList(phArgs)

# Setup Driver (excluding BlueHound)
phDriver = lib.phDatabase.setup_database_conn(phArgs)

# Execute Jobs in Task List
lib.phTasks.TaskExecution(phTaskList, phDriver, phArgs)

# Close the neoj4 connection.
lib.phDatabase.close_database_con(phArgs,phDriver)

