#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phNotifyArgs.py) - Check and Notify of CL arguments
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

from lib.phLoggy import Loggy as Loggy

def NotifyArgs(phArgs):
	Loggy(phArgs.verbose,100, "PlumHound")
	Loggy(phArgs.verbose,100, "--------------------------------------")
	Loggy(phArgs.verbose,100, "Server:" + str(phArgs.server))
	Loggy(phArgs.verbose,100, "User:" + str(phArgs.username))
	Loggy(phArgs.verbose,100, "Password: *****")
	if phArgs.UseEnc:
		Loggy(phArgs.verbose,100, "Encryption: True")
	else:
		Loggy(phArgs.verbose,100, "Encryption: False")
	Loggy(phArgs.verbose,100, "Timeout: " + str(phArgs.timeout))
	
	Loggy(phArgs.verbose,100, "--------------------------------------")
	
	if phArgs.TaskFile:
		Loggy(phArgs.verbose,100, "Tasks: Task File")
		Loggy(phArgs.verbose,100, "TaskFile: " + str(phArgs.TaskFile))
	
	if phArgs.QuerySingle:
		Loggy(phArgs.verbose,100, "Task: Single Query")
		Loggy(phArgs.verbose,100, "Query Title: " + str(phArgs.title))
		Loggy(phArgs.verbose,100, "Query Format: " + str(phArgs.OutFormat))
		Loggy(phArgs.verbose,100, "Query Path: " + str(phArgs.path))
		Loggy(phArgs.verbose,100, "Query Cypher: " + str(phArgs.QuerySingle))
	
	if phArgs.BusiestPath:
		Loggy(phArgs.verbose,100, "Task: Busiest Path")
		Loggy(phArgs.verbose,100, "Argument 1: " + str(phArgs.BusiestPath[0]))
		Loggy(phArgs.verbose,100, "Argument 2: " + str(phArgs.BusiestPath[1]))
	
	if phArgs.AnalyzePath:
		Loggy(phArgs.verbose,100, "Task: Analyzer Path")
		Loggy(phArgs.verbose,100, "Start Node: " + str(phArgs.AnalyzePath[0].upper()))
	
	if phArgs.easy:
		Loggy(phArgs.verbose,100, "Task: Easy")
		Loggy(phArgs.verbose,100, "Query Title: Domain Users")
		Loggy(phArgs.verbose,100, "Query Format: STDOUT")
		Loggy(phArgs.verbose,100, "Query Cypher: MATCH (n:User) RETURN n.name, n.displayname")
		
		Loggy(phArgs.verbose,100, "--------------------------------------")

	return True
