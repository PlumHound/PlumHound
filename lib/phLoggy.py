#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phLoggy.py) - Logging Function
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Loggy Function for lazy debugging

import datetime

def Loggy(hurdle, level, notice):
    logfile="log/PlumHound.log"
    if level <= hurdle:
        if level <100: 
            print("" + "\t" + notice)
        elif level == 100:
            print("INFO" + "\t" + notice)
        else:
            print(str(level) + "\t" + notice)

    fsys = open(logfile, "a")
    fsys.writelines(str(level) + "\t" + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S") +"\t" + notice +"\n")
    fsys.close
