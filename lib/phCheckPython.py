#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phCheckPython.py) - Check for appropriate version of python
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

import sys
from lib.phLoggy import Loggy as Loggy

def CheckPython():
    if sys.version_info < (3, 0, 0):
        print(__file__ + ' requires Python 3, while Python ' + str(sys.version[0] + ' was detected. Terminating. '))
        sys.exit(1)
        
    if sys.hexversion > 0x3090000:
        Loggy(phArgs.verbose,100, "Python Hex Version Identified:"+str(sys.hexversio))

