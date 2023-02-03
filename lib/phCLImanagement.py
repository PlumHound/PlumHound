#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phCLIManagement.py) - Management of Command Line Arguments
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

# Import Python Modules
import argcomplete
import argparse

def SetupArguments(ph_version):
    parser = argparse.ArgumentParser(description="BloodHound Wrapper for Blue/Purple Teams "+str(ph_version), add_help=True, epilog="For more information see https://github.com/plumhound")
    argcomplete.autocomplete(parser)
    
    pgroupc = parser.add_argument_group('DATABASE')
    pgroupc.add_argument("-s", "--server", type=str, help="Neo4J Server", default="bolt://localhost:7687")
    pgroupc.add_argument("-u", "--username", default="neo4j", type=str, help="Neo4J Database Useranme")
    pgroupc.add_argument("-p", "--password", default="neo4jneo4j", type=str, help="Neo4J Database Password")
    pgroupc.add_argument("--UseEnc", default=False, dest="UseEnc", help="Use encryption when connecting.", action='store_true')
    pgroupc.add_argument("--timeout", type=int, default="300", dest="timeout", help="Cypher Query Timeout **NOT FULLY IMPLEMENTED**")

    pgroupx = parser.add_mutually_exclusive_group(required="True")
    pgroupx.add_argument("--easy", help="Test Database Connection, Returns Domain Users to stdout", action='store_true')
    pgroupx.add_argument("-x", "--TaskFile", dest="TaskFile", type=str, help="Specify a PlumHound TaskList File")
    pgroupx.add_argument("-q", "--QuerySingle", dest="QuerySingle", type=str, help="Specify a Single Cypher Query")
    pgroupx.add_argument("-bp", "--BusiestPath", dest="BusiestPath", nargs='+', default=False, type=str, help="Find the X Shortest Paths that give the most users a path to Domain Admins. Need to specified [short|all] for shortestpath and the number of results. Ex: PlumHound -cu all 3")
    pgroupx.add_argument("-ap", "--AnalyzePath", dest="AnalyzePath", nargs='+', default=False, type=str, help="Analyze 'Attack Paths' between two nodes and find which path needs to be remediated to brake the path.")

    pgroupo = parser.add_argument_group('OUTPUT', "Output Options (For single cypher queries only. --These options are ignored when -x or --easy is specified.")
    pgroupo.add_argument("-t", "--title", dest="title", default="Adhoc Query", type=str, help="Report Title for Single Query [HTML,CSV,Latex]")
    pgroupo.add_argument("--of", "--OutFile", dest="OutFile", default="PlumHoundReport", type=str, help="Specify a Single Cypher Query")
    pgroupo.add_argument("--op", "--OutPath", dest="path", default="reports//", type=str, help="Specify an Output Path for Reports")
    pgroupo.add_argument("--ox", "--OutFormat", dest="OutFormat", default="STDOUT", type=str, help="Specify the type of output.", choices=['stdout', 'HTML', 'CSV', 'HTMLCSV'])

    pgrouph = parser.add_argument_group('HTML', "Options for HTML Output (For single queries or TaskLists")
    pgrouph.add_argument("--HTMLHeader", dest="HTMLHeader", type=str, default="template//head.html", help="HTML Header (file) of Report")
    pgrouph.add_argument("--HTMLFooter", dest="HTMLFooter", type=str, default="template//tail.html", help="HTML Footer (file) of Report")
    pgrouph.add_argument("--HTMLCSS", dest="HTMLCSS", type=str, default="template//html.css", help="Specify a CSS template for HTML Output")

    pgroupv = parser.add_argument_group('VERBOSE', "Set verbosity")
    pgroupv.add_argument("-v", "--verbose", type=int, default="100", help="Verbosity 0-1000, 0 = quiet, default=100, info=150, verbose=1000")

    args = parser.parse_args()

    return args

