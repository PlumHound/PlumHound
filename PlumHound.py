#!/usr/bin/env python


# PlumHound https://github.com/DefensiveOrigins/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHound Wrapper for Purple Teams
# ToolDropped May 13th 2020 as Proof of Concept Code - Black Hills Information Security #BHInfoSecurity #DefensiveOGs
#  - Community involvement: Will routinely review pull requestd.  Contributers welcome.
#  - Written in VS, haters :)  Python 3.8, see requirements.txt (pip3 install -r requirements.txt)
# GNU GPL 3.0

# PROOF OF CONCEPT CODE - ALPHA 
#Still needs work:
# the job tasklist and recordset lists should be moved into a single job task instead of mulitple variables passed in list dependent on list order
# - pathfinding queries are a headache.  until I can parse them properly I should just dump the ouput to raw so it could still be valuable.  currently the parsing will choke
# - same as above if query returns an object without specifying object keys, the object itself is a node list that parsing chokes on, currently just avoiding those queries
#  - finish arguments for CLI
# - need to add title to HTML tables so the HTML report has context
# - need a better way of grep output, throwing into parser is possibly redeundant and the entire recordset might be better just thrown into a file raw

# App Flow
# Read Task List (Or cypher query)
# Connect to Neo4JS database
# Execute tasks from tasklist
#   -> Execute Cypher Queries, export to report type (HTLM, etc)
# Close Database query

#imports
from neo4j import GraphDatabase
import argparse
import sys
import ast
from tabulate import tabulate
import csv

#ArgumentSetups
parser = argparse.ArgumentParser(description="BloodHound Wrapper for Purple Teams",add_help=True)
pgroupc = parser.add_argument_group('DATABASE')
pgroupc.add_argument("-s", "--server", type=str, help="Neo4J Server", default="bolt://localhost:7687")
pgroupc.add_argument("-u", "--username", default="neo4j", type=str, help="Neo4J Database Useranme")
pgroupc.add_argument("-p", "--password", default="neo4j1", type=str, help="Neo4J Database Password")

pgroupt = parser.add_argument_group('TASKS', "Task Selection")
pgroupt.add_argument("--easy", help="Use a sample Cypher Query Exported to STDOUT",action='store_true')
pgroupt.add_argument("-x", "--TaskFile", dest="TaskFile", type=str, help="PlumHound Plan of Cypher Queries")
pgroupt.add_argument("-c," "--QuerySingle", dest="querysingle", default="neo4j", type=str, help="Specify a Single cypher Query")

pgroupt = parser.add_argument_group('SINGLE QUERY', "Extended Options for Single Cypher Query Wrapping")
pgroupt.add_argument("-t", "--title", dest="title", default="Adhoc Query", type=str, help="Report Title for Single Query [HTML,CSV,Latex]")

pgroupo = parser.add_argument_group('OUTPUT', "Output Options")
pgroupo.add_argument("--of", "--OutFile", dest="OutFile", default="PlumHoundReport", type=str, help="Specify a Single Cypher Query")
pgroupo.add_argument("--op", "--OutPath", dest="path", default="reports\\", type=str, help="Specify an Output Path for Reports")
pgroupo.add_argument("--ox", "--OutFormat", dest="OutFormat", default="stdout", type=str, help="Specify the type of output", choices=['stdout','grep', 'HTML', 'CSV'])

pgrouph = parser.add_argument_group('HTML',"Options for HTML Output")
pgrouph.add_argument("--HTMLHeader", dest="HTMLHeader", type=str, help="HTML Header (file) of Report")
pgrouph.add_argument("--HTMLFooter", dest="HTMLFooter", type=str, help="HTML Footer (file) of Report")
pgrouph.add_argument("--HTMLCSS", dest="HTMLCSS", type=str, help="Specify a CSS template for HTML Output")

pgroupv = parser.add_argument_group('VERBOSE' "Set verbosity")
pgroupv.add_argument("-v", "--verbose", type=int, default="100", help="Verbosity 0-1000, 0 = quiet")

#push args into namespace
args = parser.parse_args()


#Bypassing ArgParse in IDE for Testing 
#server ="bolt://localhost:7687"
#username = "neo4js"
#password = 'neo4js'
#Easy = False
#TaskFile = "tasks\\Default.tasks"
#TaskFile = False
#QuerySingle = False
#Title = ""
#OutFile = "test.txt"
#OutputPath = "reports\\"
#OutFormat = "HTML"
#HTMLHeader= False
#HTMLFooter = False
#HTMLCSS = "\\template\\html.css"
#verbose = 100

#Loggy Function for lazy debugging
def Loggy(level,notice):
    if level <= args.verbose: 
        if level<=100: print("[*]" + notice)
        elif level<500: print ("[!]" + notice)
        else: print ("[*]" + notice)

   
#Setup Database Connection
def setup_database_conn(server,username,password):
    Loggy(500,"Setting up database driver")
    try:
        Loggy(200,"[!] Attempting to connect to your Neo4j project using {}:{} @ {}.".format(username, password, server))
        driver_connection = GraphDatabase.driver(server, auth=(username, password))
        Loggy(200,"[+] Success!")
        return driver_connection
    except:
        Loggy(100,"Its all gone wrong :(")
        neo4j_driver = None
        Loggy(100,"[X] Database connection failed!")
        exit()

#Setup Query 
def execute_query(driver, query, enabled=True):
    Loggy(500,"Fire Ze Misiles")
    Loggy(500,"Executing things")
    
    with driver.session() as session:
        Loggy(500,"Running Query")
        results = session.run(query)
        if check_records(results):
            count=results.detach()
            Loggy(500,"Identified "+ str(count) + " Results")
        else:
            Loggy(200,"Shoot, nothing interesting was found")
    Loggy(500,"02-z exit")
    return results

#Grab Keys for Cypher Query
def GetKeys(driver, query, enabled=True):
    Loggy(500,"Locating Keys")
    Loggy(500,"GetKeys Query:" + str(query))
    Loggy(500,"Fire Ze Misiles")
    with driver.session() as session:
        results = session.run(query)
        if check_records(results):
            keys=results.keys()
            Loggy(500,"Identified Keys:"+ str(keys))
        else:
            Loggy(200,"No Keys found, this won't go well")
            keys=0
    Loggy(500,"Key enumeartion complete")
    return keys

# Was anything found?
def check_records(results):
    """Checks if the Cypher results are empty or not."""
    if results.peek():
        Loggy(500,"Peeking at things")
        return True
    else:
        Loggy(200,"Nothing found to peek at")
        return False

#Move data from recordset to list
def processresults(results):
    Loggy(500,"Results need washed")
    BigTable = ""
    for record in results:
        try:
            #Loggy(500, "[+]"+record["n.name"])
            #Loggy(100,str(record.values()))
            BigTable = BigTable + str(record.values()) +","
        except:
            Loggy(200,"Washing records failed.  Error on record") 
    return BigTable

#File Update
def updatefile(file,update):
    Loggy(500, "Writing to disk -- File Update " + file +" " + update)
    fsys = open(file,"a")
    fsys.write(update + "\n")
    Loggy(500, "Consider it Jotted "+file)
      
#Setup Driver
newdriver = setup_database_conn(args.server,args.username,args.password)

#Build the tasklist
def MakeTaskList():
    Loggy(100,"Building Task List")

    tasks = []

    if args.TaskFile:
        Loggy(500,"Tasks file specified.  Reading")
        with open(args.TaskFile) as f:
            tasks = f.read().splitlines()
        Loggy(500,"TASKS: "+ str(tasks))
        return tasks
        
    if args.querysingle:
        Loggy(500,"Tasks Single Query Specified. Reading")
        Loggy(500,"Tasks-Title:" + args.title)
        Loggy(500,"Tasks-OutFormat:" + args.OutFormat)
        Loggy(500,"Tasks-OutPath:" + args.OutPath)
        Loggy(500,"Tasks-QuerySingle:" + args.querysingle)
        tasks.append(args.title,args.OutFormat,args.OutPath,args.querysingle)
        return tasks
            
    if args.easy:
        Loggy(500,"Tasks Easy Query Specified.")
        tasks = ['["Domain Users","STDOUT","","MATCH (n:User) RETURN n.name, n.displayname"]']
        return tasks
        
    Loggy(100,"Tasks Generation Completed\nTasks: " + str(tasks))

    return tasks
    # Basic default query bits will be specified here

#Start Executions
def TaskExecution(tasks,Outpath,HTMLHeader,HTMLFooter,HTMLCSS):
     Loggy(500,"Begin Task Executions")
     Loggy(500,"TASKS:/n" + str(tasks))

     jobHTMLHeader = HTMLHeader
     jobHTMLFooter = HTMLFooter
     jobHTMLCSS = HTMLCSS

     for job in tasks:
        try:
            Loggy(200,"Starting job")
            Loggy(500,"Job: "+str(job))

            job_List = ast.literal_eval(job) 
            jobTitle = job_List[0]
            jobOutFormat = job_List[1]
            jobOutPathFile = Outpath + job_List[2]
            jobQuery = job_List[3]

            Loggy(500,"Job Title: "+jobTitle)
            Loggy(500,"Job Format: "+jobOutFormat)
            Loggy(500,"Job File: "+jobOutPathFile)
            Loggy(500,"Job Query: "+jobQuery)

            jobkeys = GetKeys(newdriver,jobQuery)
            jobkeys_List = ast.literal_eval(str(jobkeys))
            #Quick fix if keys returned no record sto properly rebuild the keys list as 0 records, instead of int(0)
            if isinstance(jobkeys_List,int): jobKeys_List=[]
       
            jobresults = execute_query(newdriver,jobQuery)
            jobresults_processed= "[" +processresults(jobresults) + "]"

            try:
                jobresults_processed_list = ast.literal_eval(jobresults_processed)
            except:
                Loggy(200,"ERROR: Something Broke trying to deal with pathfinding.")
                Loggy(500,jobresults_processed)
                #jobresults_processed_list = ast.literal_eval("'"+jobresults_processed+"'")
                jobresults_processed_list = jobresults_processed

            Loggy(500,"Calling delievery service")
            SenditOut(jobkeys_List,jobresults_processed_list,jobOutFormat,jobOutPathFile,"",jobTitle,jobHTMLHeader,jobHTMLFooter,jobHTMLCSS)
        except:
            Loggy(200,"ERROR: Soemthing broke trying to parse jobs (move along).")



def SenditOut(list_KeysList,Processed_Results_List,OutFormat,OutFile,OutPath,Title,HTMLHeader,HTMLFooter,HTMLCSS):
    #Send the output as specified.
    #Quick fix if keys returned no records to properly rebuild the keys list as 0 records, instead of int(0)

    if isinstance(list_KeysList,int): list_KeysList=[]
    output = ""

    if OutFormat == "CSV":
        Loggy(100, "Beginning Output CSV:" + OutFile)
        with open("OutPath+OutFile", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(list_KeysList)
            writer.writerows(Processed_Results_List)    
        return True

    if OutFormat == "STDOUT":
        #STDOUT
        print()
        output=tabulate(Processed_Results_List,list_KeysList,tablefmt="simple")
        print(output)
        return True

    if OutFormat == "HTML":
        Loggy(100, "Beginning Output HTML:" + OutFile)
 
        output=tabulate(Processed_Results_List,list_KeysList,tablefmt="html")
        HTMLCSS_str = ""
        HTMLHeader_str = ""
        HTMLFooter_str = ""
        HTMLPre_str="<HTML><head>"
        HTMLMId_str="</head><Body>"
        HTMLEnd_str="</body></html>"
        if HTMLHeader: 
            with open(HTMLHeader, 'r') as header: HTMLHeader_str = header.read()

        if HTMLFooter: 
            with open(HTMLFooter, 'r') as footer: HTMLFooter_str = footer.read()

        if HTMLCSS:
            with open(HTMLCSS, 'r') as css: HTMLCSS_str = "<style>\n" + css.read() + "\n</style>"

        Loggy(500, "File Writing " + OutPath+OutFile)
        output = HTMLPre_str + HTMLCSS_str + HTMLMId_str + HTMLHeader_str + output + HTMLFooter_str +HTMLEnd_str
        fsys = open(OutPath+OutFile,"w")
        fsys.write(output)
        fsys.close
        return True

    if OutFormat == "GREP":
        Loggy(100, "Beginning Output Grep:" + args.OutFile)
        fsys = open(OutPath+OutFile,"w")
        fsys.write(output)
        fsys.close
        return True

#Read Task List
Loggy(500,"Start Task Generation")
TaskList = MakeTaskList()
Loggy(500,"TASKS:/n"+str(TaskList))

#Start Task List
Loggy(500,"Start Task Execution")
TaskExecution(TaskList,args.path,args.HTMLHeader,args.HTMLFooter,args.HTMLCSS)
Loggy(500,"Tasks Completed")

#Close out neo4j connection
newdriver.close

#END



