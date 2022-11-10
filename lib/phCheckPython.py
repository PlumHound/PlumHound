#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phCheckPython.py) - Check for appropriate version of python
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

import sys

def CheckPython():
    if sys.version_info < (3, 0, 0):
        print(__file__ + ' requires Python 3, while Python ' + str(sys.version[0] + ' was detected. Terminating. '))
        sys.exit(1)
        
    if sys.hexversion > 0x3090000:
        print()
        print('WARN: Python hexversion %s is in use.' % hex(sys.hexversion))
        # print('WARN: Plumhound may have unexpected behavior. Use > 0x3000000 < 0x30a0000')
        # commented while I figure a better way to confirm python version
        print()
