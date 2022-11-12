#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phDatabase.py) Database Connection Management
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

from neo4j import GraphDatabase
from lib.phLoggy import Loggy as Loggy

# Setup Database Connection
def setup_database_conn(phArgs):
    Loggy(phArgs.verbose,900, "------ENTER: SETUP_DATABASE_CONN-----")
    Loggy(phArgs.verbose,200, "[!] Attempting to connect to your Neo4j project using {}:{} @ {} {}.".format(phArgs.username, phArgs.password, phArgs.server, "[ENCRYPTED]" if phArgs.UseEnc else "[UNECNCRYPTED]"))
    try:
        if phArgs.UseEnc:
            Loggy(phArgs.verbose,200, " Using Neo4j encryption")
            driver_connection = GraphDatabase.driver(phArgs.server, auth=(phArgs.username, phArgs.password), encrypted=True)
        else:
            Loggy(phArgs.verbose,200, " Not using Neo4j encryption")
            driver_connection = GraphDatabase.driver(phArgs.server, auth=(phArgs.username, phArgs.password), encrypted=False)
        Loggy(phArgs.verbose,200, "[+] Success!")
        return driver_connection
    except Exception:
        Loggy(phArgs.verbose,100, "There was a problem. Check username, password, and server parameters.")
        Loggy(phArgs.verbose,100, "[X] Database connection failed!")
        exit()
    Loggy(phArgs.verbose,900, "------EXIT: SETUP_DATABASE_CONN-----")

def close_database_con(phArgs,connectiondriver):
    Loggy(phArgs.verbose,900, "------ENTER: CLOSE_DATABASE_CONN-----")
    connectiondriver.close
    Loggy(phArgs.verbose,200, "[+] Closed Database Connection!")
    Loggy(phArgs.verbose,900, "------EXIT: CLOSE_DATABASE_CONN-----")
    exit()
