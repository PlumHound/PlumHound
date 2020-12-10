#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phLoggy.py) - Logging Function
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Loggy Function for lazy debugging
def Loggy(hurdle, level, notice):
    if level <= hurdle:
        if level <= 100:
            print("INFO" + "\t" + notice)
        else:
            print(level + "\t" + notice)