#!/usr/bin/env python
# -*- coding: utf8 -*-

# PlumHound v01.070a

# PlumHound https://github.com/DefensiveOrigins/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHound Wrapper for Purple Teams
# ToolDropped May 13th 2020 as Proof of Concept Code - Black Hills Information Security #BHInfoSecurity #DefensiveOGs

# GNU GPL 3.0

#Import PlumHound Components
from phlib.plumcode import *

#Check for Python3 environment.
CheckPython()

#SetupArguments
SetupArguments()

#Setup Driver
newdriver = setup_database_conn(args.server,args.username,args.password)

#Read Task List
TaskList = MakeTaskList()

#Start Task List
TaskExecution(TaskList,args.path,args.HTMLHeader,args.HTMLFooter,args.HTMLCSS)

#Close out neo4j connection
newdriver.close

#END
