#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phLoggy.py) - Logging Function
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Loggy Function for lazy debugging

import sys
from datetime import date

def Loggy(hurdle, level, notice):
    if level <= hurdle:
        if level <= 100:
            print("INFO" + "\t" + notice)
        else:
            print(str(level) + "\t" + notice)

    fsys = open("log\\PlumHound.log", "w")
    fsys.writelines(str(level) + "\t" datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S") +"\t" + notice)
    fsys.close
