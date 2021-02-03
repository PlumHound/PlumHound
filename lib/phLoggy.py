#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phLoggy.py) - Logging Function
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Loggy Function for lazy debugging

import datetime
from typing import Callable


class Loggy():
    hurdle = 0
    logfile = "log/PlumHound.log"

    @staticmethod
    def log(level: int, message: str):
        if level <= Loggy.hurdle:
            if level <= 100:
                print("INFO\t" + message)
            else:
                print(str(level) + "\t" + message)

        fsys = open(Loggy.logfile, "a")
        fsys.writelines(str(level) + "\t" + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S") + "\t" + message + "\n")
        fsys.close


def set_log_hurdle(hurdle: int):
    Loggy.hurdle = hurdle


def log_calls(fn: Callable) -> Callable:
    def wrap(*args, **kwargs):
        Loggy.log(900, f'----ENTER: {fn.__name__}----')
        result = fn(*args, **kwargs)
        Loggy.log(900, f'----EXIT: {fn.__name__}----')
        return result
    return wrap


loggy = Loggy.log
