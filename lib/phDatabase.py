#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phDatabase.py) Database Connection Management
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

from neo4j import GraphDatabase
from lib.phLoggy import loggy, log_calls


# Setup Database Connection
@log_calls
def setup_database_conn(phArgs):
    loggy(200, "[!] Attempting to connect to your Neo4j project using {}:{} @ {} {}.".format(phArgs.username, phArgs.password, phArgs.server, "[ENCRYPTED]" if phArgs.UseEnc else "[UNECNCRYPTED]"))
    try:
        if phArgs.UseEnc:
            loggy(200, " Using Neo4j encryption")
            driver_connection = GraphDatabase.driver(phArgs.server, auth=(phArgs.username, phArgs.password), encrypted=True)
        else:
            loggy(200, " Not using Neo4j encryption")
            driver_connection = GraphDatabase.driver(phArgs.server, auth=(phArgs.username, phArgs.password), encrypted=False)
        loggy(200, "[+] Success!")
        return driver_connection
    except Exception:
        loggy(100, "There was a problem. Check username, password, and server parameters.")
        loggy(100, "[X] Database connection failed!")
        exit()


@log_calls
def close_database_con(phArgs, connectiondriver):
    connectiondriver.close
    loggy(200, "[+] Closed Database Connection!")
    exit()
