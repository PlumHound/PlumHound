
![PlumHound](https://raw.githubusercontent.com/DefensiveOrigins/PlumHound/master/docs/images/Plum3.jpg)

# PlumHound - BloodHoundAD Report Engine for Security Teams
Released as Proof of Concept for Blue and Purple teams to more effectively use BloodHoundAD in continual security life-cycles by utilizing the BloodHoundAD pathfinding engine to identify Active Directory security vulnerabilities resulting from business operations, procedures, policies and legacy service operations.

PlumHound operates by wrapping BloodHoundAD's powerhouse graphical Neo4J backend cypher queries into operations-consumable reports.  Analyzing the output of PlumHound can steer security teams in identifying and hardening common Active Directory configuration vulnerabilities and oversights.

## Release and call to Action
The initial PlumHound code was released on May 14th, 2020 during a Black Hills Information Security webcast, A Blue Teams Perspective on Red Team Tools.  The webcast was recorded and is available on YouTube. [A Blue Team's Perspetive on Red Team Tools](https://youtu.be/0mIN2OU5hQEs).


The PlumHound Framework yields itself to community involvement in the creation and proliferation of "TaskLists" (work) that can be shared and used across different organizations.  TaskLists contain jobs for PlumHound to do (queries to run, reports to write).  A second PlumHound community repo has been created to allow for the open sharing of TaskLists (see [Plumhound-Tasks](https://github.com/DefensiveOrigins/PlumHound-Tasks))

Looking for more tasks and templates? Checkout [PlumHound-Tasks ](https://github.com/DefensiveOrigins/PlumHound-Tasks)for the community driven marketplace of PlumHound reporting taskslists and report designs

## Background
A client of ours working on hardening their Active Directory infrastructure asked us about vulnerabilities that can be found by using BloodHound.  They had heard of the effectiveness of BloodHoundAD in Red-Team's hands and was told that BloodHound would identify all types of security mis-alignments and mis-configurations in their Active Directory environment.  We helped them through analysis of their BloodHound dataset and it became quickly evident that BloodHoundAD's pathfinding graphical database was not designed for the fast-passed analytical security team accustom to reading reports and action items.  

In fact, one of our cypher queries determined that 96% of their 3000 users had a path to Domain Admin with an average of just 4 steps.  However, that graphical query rendered over 10,000 paths to Domain Admin.  Finding the actual cause of the short-paths to DA wasn't as easy as just loading data into BloodHound or putting Cobalt Strike on Auto-Pilot with BloodHound Navigation.  
Hence, PlumHound was created out of a need to retrieve consumable data from BloodHoundAD's pathfinding engine.  Data that could yield itself to inferring actionable work for security teams to harden their environments.

## Sample Reports
The sample reports are from a BadBlood created AD environment that does not include user sessions and massive ACLs that would be typical of a larger environment.  That is, the reports a bit bare, but you get the idea.  Sample reports are found in the /reports folder.  Note that by default, this is the output location for PlumHound and will over-write reports in this location if specified by the tasklist file.

![PlumHound](https://raw.githubusercontent.com/DefensiveOrigins/PlumHound/master/docs/images/Workstations_UnrestrainedDelegation.png)
* This is a screenshot of an earlier report version.  New versions include Title, Header etc.


## PlumHound Examples
Use the default username, password, server, and execute the "Easy" task, to test connectivity.  This will output all Active Directory user objects from the Neo4J database.

```plaintext
python3 PlumHound.py --easy
```

Execute PlumHound with the Default TaskList using Default Credentials and Database.
```plaintext
python3 PlumHound.py -x tasks/default.tasks

[*]Building Task List
[*]Beginning Output HTML:reports\DomainUsers.html
[*]Beginning Output HTML:reports\Keroastable_Users.html
[*]Beginning Output HTML:reports\Workstations_RDP.html
[*]Beginning Output HTML:reports\Workstations_UnconstrainedDelegation.html
[*]Beginning Output HTML:reports\GPOs.html
[*]Beginning Output HTML:reports\AdminGroups.html
[*]Beginning Output HTML:reports\ShortestPathDA.html
[*]Beginning Output HTML:reports\RDPableGroups.html
[*]Beginning Output HTML:reports\Groups_CanResetPasswords.html
[*]Beginning Output HTML:reports\LocalAdmin_Groups.html
[*]Beginning Output HTML:reports\LocalAdmin_Users.html
[*]Beginning Output HTML:reports\DA_Sessions.html
[*]Beginning Output HTML:reports\Keroastable_Users_MostPriv.html
[*]Beginning Output HTML:reports\OUs_Count.html
[*]Beginning Output HTML:reports\Permissions_Everyone.html
[*]Beginning Output HTML:reports\Groups_MostAdminPriviledged.html
[*]Beginning Output HTML:reports\Computers_WithDescriptions.html
[*]Beginning Output HTML:reports\Users_NoKerbReq.html
[*]Beginning Output HTML:reports\Users_Count_DirectAdminComputers.html
[*]Beginning Output HTML:reports\Users_Count_InDirectAdminComputers.html
[*]Beginning Output HTML:reports\Users_NeverActive_Enabled.html
```
The same, but quiet the output (-v 0), specify the Neo4J server, useranme, and password instead of using defaults.
```plaintext
python3 PlumHound.py -x tasks/default.tasks -s "bolt://127.0.0.1:7687" -u "neo4j" -p "neo4jj" -v 0
```

Execute the Path Analyzer external function.  

Option #1 using label. The supported labels are `User`, `Group`, `Computer`, `OU` and `GPO`. This function will assume the target group is "DOMAIN ADMINS".
```plaintest
python3 PlumHound.py -ap user
```
**NOTE:** The above syntax implies you are using the default values for `sever`, `user` and `password` or that you have hardcoded them in the script.  

Option #2 specify `start node` and `end node` 
```plaintest
python3 PlumHound.py -ap "domain users@example.com" "domain admins@example.com"
```
**NOTE:** To use BlueHound Path Analyzer logic you need to get a copy of the Python script from https://github.com/scoubi/BlueHound  


## Detailed PlumHound Syntax
```plaintext
usage: PlumHound.py [-h] [-s SERVER] [-u USERNAME] [-p PASSWORD] [--UseEnc]
                    (--easy | -x TASKFILE | -q,--QuerySingle QUERYSINGLE | -bp,--BusiestPath BUSIESTPATH [BUSIESTPATH ...] | -ap,--AnalyzePath ANALYZEPATH [ANALYZEPATH ...])
                    [-t TITLE] [--of OUTFILE] [--op PATH] [--ox {stdout,HTML,CSV}] [--HTMLHeader HTMLHEADER] [--HTMLFooter HTMLFOOTER] [--HTMLCSS HTMLCSS]
                    [-v VERBOSE]

BloodHound Wrapper for Blue/Purple Teams; v01.070a

optional arguments:
  -h, --help            show this help message and exit
  --easy                Test Database Connection, Returns Domain Users to stdout
  -x TASKFILE, --TaskFile TASKFILE
                        Specify a PlumHound TaskList File
  -q,--QuerySingle QUERYSINGLE
                        Specify a Single Cypher Query
  -bp,--BusiestPath BUSIESTPATH [BUSIESTPATH ...]
                        Find the X Shortest Paths that give the most users a path to Domain Admins. Need to specified [short|all] for shortestpath and the
                        number of results. Ex: PlumHound -cu all 3
  -ap,--AnalyzePath ANALYZEPATH [ANALYZEPATH ...]
                        Analyze 'Attack Paths' between two nodes and find which path needs to be remediated to brake the path.

DATABASE:
  -s SERVER, --server SERVER
                        Neo4J Server
  -u USERNAME, --username USERNAME
                        Neo4J Database Useranme
  -p PASSWORD, --password PASSWORD
                        Neo4J Database Password
  --UseEnc              Use encryption when connecting.

OUTPUT:
  Output Options (For single cypher queries only. --These options are ignored when -x or --easy is specified.

  -t TITLE, --title TITLE
                        Report Title for Single Query [HTML,CSV,Latex]
  --of OUTFILE, --OutFile OUTFILE
                        Specify a Single Cypher Query
  --op PATH, --OutPath PATH
                        Specify an Output Path for Reports
  --ox {stdout,HTML,CSV}, --OutFormat {stdout,HTML,CSV}
                        Specify the type of output

HTML:
  Options for HTML Output (For single queries or TaskLists

  --HTMLHeader HTMLHEADER
                        HTML Header (file) of Report
  --HTMLFooter HTMLFOOTER
                        HTML Footer (file) of Report
  --HTMLCSS HTMLCSS     Specify a CSS template for HTML Output

VERBOSESet verbosity:
  -v VERBOSE, --verbose VERBOSE
                        Verbosity 0-1000, 0 = quiet

For more information see https://plumhound.DefensiveOrigins.com
```


# Database Connection
PlumHound needs to connect to the Neo4J graphing database where BloodHoundAD data was loaded.  

```plaintext
DATABASE:
  -s SERVER, --server SERVER
                        Neo4J Server
  -u USERNAME, --username USERNAME
                        Neo4J Database Useranme
  -p PASSWORD, --password PASSWORD
                        Neo4J Database Password
  --UseEnc              Use encryption when connect
```
PlumHound paramters are set by default.  You can override the default by including the argument.

| Argument/Parameter | Default |
|----------|----------|
| SERVER | bolt://localhost:7687 |
| USERNAME | neo4j |
| PASSWORD | neo4jj |



# HTML Report Design Output and Variables
HTML output includes the ability to use HTML Headers, Footers, and CSS to modify the design of the report.  Additionaly, variables can be added to the HTML Header and Footer files that are replaced at runtime. 
```plaintext
HTML:
  Options for HTML Output (For single queries or TaskLists

  --HTMLHeader HTMLHEADER
                        HTML Header (file) of Report
  --HTMLFooter HTMLFOOTER
                        HTML Footer (file) of Report
  --HTMLCSS HTMLCSS     Specify a CSS template for HTML Output
```

| Argument/Parameter | Default  |
|-----------|----------|
| HTMLHeader  | templates/head.html |
| HTMLFooter  | templates/tail.html |
| HTMLCSS  | templates/html.css |


| Variable                | Output                                   |
|-------------------------|------------------------------------------|
| --------PH_TITLE------- | Report Tile from --Title or TaskList/Job |
| --------PH_DATE------- | Python date.today()|

This allows the HTML output to be dynamic and tailored to your specification.



# TaskList Files
The PlumHound Repo includes a sample TaskList that exports some basic BloodHoundAD Cypher queries to an HTML Report.  The included tasks\Default.tasks sample shows the basic syntax of the TaskList files.  The TaskList Files allow PlumHound to be fully scripted with batch jobs after the SharpHound dataset has been imported not BloodHoundAD on Neo4j. 
Looking for more tasks and templates? Checkout [PlumHound-Tasks ](https://github.com/DefensiveOrigins/PlumHound-Tasks)for the community driven marketplace of PlumHound reporting taskslists and report designs.


## TaskList File Syntax

```plaintext
["Report Title","[Output-Format]","[Output-File]","[CypherQuery]"]
```

## TaskList Sample: default.tasks
The default.tasks file includes multiple tasks that instruct PlumHound to create reports using the specified "HTML" output format, output filename, and specific BloodHoundAD Neo4JS Cypher Query. 
```plaintext
["Domain Users HTML", "HTML", "DomainUsers.html", "MATCH (n:User) RETURN n.name as Name,n.displayname as DisplayName,n.enabled as Enabled, n.highvalue as HighValue,  n.description as Description, n.title as Title, n.pwdneverexpires as PWDNeverExpires, n.passwordnotreqd as PWDNotReqd, n.sensitive as Sensitive, n.admincount as AdminCount, n.serviceprincipalnames as SPN, toString(datetime({epochSeconds: ToInteger(coalesce(n.pwdlastset,0))})) as PWDLastSet, toString(datetime({epochSeconds: ToInteger(coalesce(n.lastlogon,0))})) as LastLogon" ]
["Keroastable Users","HTML","Keroastable_Users.html","MATCH (n:User) WHERE n.hasspn=true RETURN n.name, n.displayname,n.description, n.title, n.pwdneverexpires, n.passwordnotreqd, n.sensitive, n.admincount, n.serviceprincipalnames"]
["RDPable Servers","HTML","Workstations_RDP.html","match p=(g:Group)-[:CanRDP]->(c:Computer) where  g.objectid ENDS WITH \'-513\'  AND c.operatingsystem CONTAINS \'Server\' return c.namep"]
["Unconstrained Delegation Computers with SPN","HTML","Computers_UnconstrainedDelegation.html","MATCH (c:Computer {unconstraineddelegation:true}) return c.name as Computer, c.description as Description, c.serviceprincipalnames as SPN"]
["Admin Groups","HTML","AdminGroups.html","Match (n:Group) WHERE n.name CONTAINS \'ADMIN\' return n.name, n.highvalue, n.description, n.admincount"]
["RDPable Groups", "HTML", "RDPableGroups.html", "MATCH p=(m:Group)-[r:CanRDP]->(n:Computer) RETURN m.name as Group, n.name as Computer ORDER BY m.name" ]
["RDPable Groups Count", "HTML", "RDPableGroupsCount.html", "MATCH p=(m:Group)-[r:CanRDP]->(n:Computer) RETURN m.name as Group, count(*) as Computer ORDER BY Computer DESC" ]
["PasswordResetter Groups", "HTML", "Groups_CanResetPasswords.html", "MATCH p=(m:Group)-[r:ForceChangePassword]->(n:User) RETURN m.name as Group, n.name ORDER BY m.name as User" ]
["PasswordResetter Groups Count", "HTML", "Groups_CanResetPasswordsCount.html", "MATCH p=(m:Group)-[r:ForceChangePassword]->(n:User) RETURN m.name as Group, count(*) as Users ORDER BY Users DESC" ]
["LocalAdminGroups", "HTML", "LocalAdmin_Groups.html", "MATCH p=(m:Group)-[r:AdminTo]->(n:Computer) RETURN m.name as Group, n.name as Computer ORDER BY m.name" ]
["LocalAdminGroupsCount", "HTML", "LocalAdmin_Groups_Count.html", "MATCH p=(m:Group)-[r:AdminTo]->(n:Computer) RETURN m.name as Group, count(*) as Computer ORDER BY Computer DESC"]
["LocalAdminUsers","HTML","LocalAdmin_Users.html","MATCH p=(m:User)-[r:AdminTo]->(n:Computer) RETURN m.name as User, n.name as Computer ORDER BY m.name"]
["LocalAdminUsers", "HTML", "LocalAdmin_Users.html", "MATCH p=(m:User)-[r:AdminTo]->(n:Computer) RETURN m.name as User, count(*) as Computer ORDER BY Computer DESC" ]
["Users Sessions"HTML", "Users_Sessions.html", "MATCH p=(n:User)--(c:Computer)-[:HasSession]->(n) return n.name as User,  c.name as Computer ORDER BY n.name"]
["Users Sessions Count"HTML", "Users_Sessions_Count.html", "MATCH p=(n:User)--(c:Computer)-[:HasSession]->(n) return n.name as User, count(*) as Computers ORDER BY Computers DESC"]
["Cross Domain Relationships"HTML", "CrossDomainRelationships.html", "MATCH (n)-[r]->(m) WHERE NOT n.domain = m.domain RETURN LABELS(n)[0] as Dom1Object ,n.name as Object1 ,TYPE(r) as Relationship ,LABELS(m)[0] as Dom2Object,m.name as Object2"]
["DA Sessions","HTML","DA_Sessions.html","MATCH (n:User)-[:MemberOf]->(g:Group) WHERE g.objectid ENDS WITH \'-512\' MATCH p = (c:Computer)-[:HasSession]->(n) return g.name, c.name"]
["Keroastable Most Priv","HTML","Keroastable_Users_MostPriv.html","MATCH (u:User {hasspn:true}) OPTIONAL MATCH (u)-[:AdminTo]->(c1:Computer) OPTIONAL MATCH (u)-[:MemberOf*1..]->(:Group)-[:AdminTo]->(c2:Computer) WITH u,COLLECT(c1) + COLLECT(c2) AS tempVar UNWIND tempVar AS comps RETURN u.name as KeroastableUser,COUNT(DISTINCT(comps)) as Computers ORDER BY COUNT(DISTINCT(comps)) DESC"]
["OUs By Computer Member Count","HTML","OUs_Count.html","MATCH (o:OU)-[:Contains]->(c:Computer) RETURN o.name as OU,COUNT(c) as Computers ORDER BY COUNT(c) DESC"]
["Permissions for Everyone and Authenticated Users","HTML","Permissions_Everyone.html","MATCH p=(m:Group)-[r:AddMember|AdminTo|AllExtendedRights|AllowedToDelegate|CanRDP|Contains|ExecuteDCOM|ForceChangePassword|GenericAll|GenericWrite|GetChanges|GetChangesAll|HasSession|Owns|ReadLAPSPassword|SQLAdmin|TrustedBy|WriteDACL|WriteOwner|AddAllowedToAct|AllowedToAct]->(t) WHERE m.objectsid ENDS WITH \'-513\' OR m.objectsid ENDS WITH \'-515\' OR m.objectsid ENDS WITH \'S-1-5-11\' OR m.objectsid ENDS WITH \'S-1-1-0\' RETURN m.name,TYPE(r),t.name,t.enabled"]
["Most Admin Priviledged Groups","HTML","Groups_MostAdminPriviledged.html","MATCH (g:Group) OPTIONAL MATCH (g)-[:AdminTo]->(c1:Computer) OPTIONAL MATCH (g)-[:MemberOf*1..]->(:Group)-[:AdminTo]->(c2:Computer) WITH g, COLLECT(c1) + COLLECT(c2) AS tempVar UNWIND tempVar AS computers RETURN g.name AS GroupName,COUNT(DISTINCT(computers)) AS AdminRightCount ORDER BY AdminRightCount DESC"]
["Computers with Descriptions","HTML","Computers_WithDescriptions.html","MATCH (c:Computer) WHERE c.description IS NOT NULL RETURN c.name,c.description"]
["User No Kerb Needed","HTML","Users_NoKerbReq.html","MATCH (n:User {dontreqpreauth: true}) RETURN n.name, n.displayname, n.description, n.title, n.pwdneverexpires, n.passwordnotreqd, n.sensitive, n.admincount, n.serviceprincipalnames"]
["Users Computer Direct Admin Count","HTML","Users_Count_DirectAdminComputers.html","MATCH (u:User)-[:AdminTo]->(c:Computer) RETURN count(DISTINCT(c.name)) AS COMPUTER, u.name AS USER ORDER BY count(DISTINCT(c.name)) DESC"]
["Users Computer InDirect Admin Count","HTML","Users_Count_InDirectAdminComputers.html","MATCH (u:User)-[:AdminTo]->(c:Computer) RETURN count(DISTINCT(c.name)) AS COMPUTER, u.name AS USER ORDER BY count(DISTINCT(c.name)) DESC"]
["NeverActive Active Users","HTML","Users_NeverActive_Enabled.html","MATCH (n:User) WHERE n.lastlogontimestamp=-1.0 AND n.enabled=TRUE RETURN n.name ORDER BY n.name"]
["Users GPOs Access Weirdness","HTML","Users_GPO_CheckACL.html","MATCH p=(u:User)-[r:AllExtendedRights|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|GpLink*1..]->(g:GPO) RETURN p LIMIT 25"]"]
["Servers in OUs","HTML","ServersInOUs.html","MATCH (o:OU)-[:Contains]->(c:Computer) WHERE toUpper(c.operatingsystem) STARTS WITH "WINDOWS SERVER" RETURN o.name as OU,c.name as Computer,c.operatingsystem as OS"]
["Operating Systems Count","HTML","OperatingSystemCount.html","MATCH (c:Computer) RETURN c.operatingsystem aS OS, count(*) as Computers ORDER BY Computers DESC"]
["LAPS Deployment Count","HTML","LapsDeploymentCount.html","MATCH (c:Computer) RETURN c.haslaps as LAPSEnabled, count(*) as Computers ORDER BY Computers DESC"]
["LAPS Not Enabled","HTML","LapsNotEnabled.html","MATCH (c:Computer) WHERE c.haslaps=false RETURN c.haslaps as LAPSEnabled, c.name as Computer ORDER BY Computer"]
["Domain List","HTML","Domains.html","MATCH (n:Domain) return n.name as Domain, n.functionallevel as FunctionalLevel, n.highvalue as HighValue, n.domain as DNS"]
["Operating Systems Unsupported","HTML","OperatingSystemUnsupported.html","MATCH (c:Computer) WHERE c.operatingsystem =~ '.*(2000|2003|2008|xp|vista|7|me).*' RETURN c.name as Computer, c.operatingsystem as UnsupportedOS, c.enabled as Enabled"]
["GPOs","HTML","GPOs.html","Match (n:GPO) return n.name as GPO, n.highvalue as HighValue, n.gpcpath as Path"]
["HighValue Group Members","HTML","Groups-HighValue-members.html","MATCH p=(n:User)-[r:MemberOf*1..]->(m:Group {highvalue:true}) RETURN n.name as User, m.name as Group"]
["Add Use Delegation","HTML","User-AddToGroupDelegation.html","MATCH (n:User {admincount:False}) MATCH p=allShortestPaths((n)-[r:AddMember*1..]->(m:Group)) RETURN n.name as User, m.name as Group"]
```

# Busiest Path
The Busiest Path(s) function takes two parameters 
1- `all` or `short` either you want to use `shortestpath` or `allshorteshpaths` algorithym. 
2- The number of results you want to return. ex: Top 5

```plaintext
python3 PlumHound.py -bp short 5
[*]Building Task List
[51, 'IT00385@BTV.ORG']
[51, 'IT00346@BTV.ORG']
[50, 'IT01186@BTV.ORG']
[49, 'IT00435@BTV.ORG']
[49, 'IT00333@BTV.ORG']
[*]Tasks Generation Completed
Tasks: []
```

# Analyze Path
The Analyze Path takes either a `label` or a `start node` and `end node` and loop through all the paths finding which relationship(s) need to be broken in order to break the whole path. This is useful when you want to provide your AD Admins with concrete actions they can take in order to improuve your overall AD Security Posture. 

```plaintext
python3 PlumHound.py -ap group
[...]
---------------------------------------------------------------------
Analyzing paths between IT00738@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
Removing the relationship CanRDP between IT00738@BTV.ORG and COMP00886.BTV.ORG breaks the path!
Removing the relationship HasSession between COMP00886.BTV.ORG and EKRITIKOS00681@BTV.ORG breaks the path!
---------------------------------------------------------------------
Analyzing paths between IT00803@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
---------------------------------------------------------------------
Analyzing paths between IT00854@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
---------------------------------------------------------------------
Analyzing paths between IT00870@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
Removing the relationship ExecuteDCOM between IT00870@BTV.ORG and COMP00629.BTV.ORG breaks the path!
Removing the relationship HasSession between COMP00629.BTV.ORG and YWINES00123@BTV.ORG breaks the path!
Removing the relationship MemberOf between YWINES00123@BTV.ORG and HR01256@BTV.ORG breaks the path!
Removing the relationship MemberOf between HR01256@BTV.ORG and IT01085@BTV.ORG breaks the path!
---------------------------------------------------------------------
Analyzing paths between IT00874@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
Removing the relationship AdminTo between IT00874@BTV.ORG and COMP01055.BTV.ORG breaks the path!
Removing the relationship HasSession between COMP01055.BTV.ORG and LJARAD00311@BTV.ORG breaks the path!
Removing the relationship MemberOf between LJARAD00311@BTV.ORG and HR00694@BTV.ORG breaks the path!
Removing the relationship MemberOf between HR00694@BTV.ORG and IT01182@BTV.ORG breaks the path!
Removing the relationship AdminTo between IT01182@BTV.ORG and COMP00658.BTV.ORG breaks the path!
Removing the relationship AllowedToDelegate between COMP00658.BTV.ORG and COMP01387.BTV.ORG breaks the path!
Removing the relationship AllowedToDelegate between COMP01387.BTV.ORG and COMP00275.BTV.ORG breaks the path!
Removing the relationship HasSession between COMP00275.BTV.ORG and RHETZLER01120@BTV.ORG breaks the path!
Removing the relationship MemberOf between RHETZLER01120@BTV.ORG and DOMAIN ADMINS@BTV.ORG breaks the path!
---------------------------------------------------------------------
Analyzing paths between IT00487@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
---------------------------------------------------------------------
Analyzing paths between IT00547@BTV.ORG and DOMAIN ADMINS@BTV.ORG
---------------------------------------------------------------------
[...]
```

# Hat-Tips & Acknowledgements
* [Hausec's Cypher Query CheatSheet](https://hausec.com/2019/09/09/bloodhound-cypher-cheatsheet/)  gave us a headstart on some decent pathfinding cypher queries.  | [Git](https://github.com/hausec)
* [SadProcessor's Blue Hands on BloodHound](https://github.com/SadProcessor/WatchDog) gave us a detailed primer on BloodHoundAD's ability to lead a BlueTeam to water. | [Git](https://github.com/SadProcessor).
* Additional work by SadProcessor with [Cypher Dog 3.0](https://github.com/SadProcessor/CypherDog) shows similar POC via utilizing BloodHoundAD's Cypher Queries with a RestAPI endpoint via PowerShell.  PlumHound operates similarly however written in python and designed for stringing multiple queries into consumable reports designed to infer actionable items. 
* [BloodHoundAD](https://github.com/BloodHoundAD/BloodHound): We wouldn't be talking about this at all if it weren't for the original BloodHoundAD work.  BloodHound is developed by @_wald0, @CptJesus, and @harmj0y.
* "Band-aids don't fix dank domains."  [BadBlood](https://github.com/davidprowe/BadBlood) saved us a ton of time building realistic-enough AD domains for testing. @davidprowe  
* [BloodHound from Red to Blue](https://www.youtube.com/watch?v=-HPhJw9K6_Y) - Scoubi- Mathieu Saulnier -- About a month after we released PlumHound POC we ran into Scoubi who was working on a similar project, BlueHound, but hadn't yet publicly released it. He's planning to Release at SecTor 2020. Despite we hadn't met, I found enough similarities between our goals that I felt it would be inappropriate not to credit Mathieu for driving the industry that ultimately lead us to build PlumHound.  Check out his DerbyCon talk and be on the lookout at SecTor.



# Installation Requirements (python 3.7/3.8)
* apt-get install python3
* pip3 install -r requirements.txt


# Environment Setup Instructions
* Install Neo4JS
* Install BloodhoundAD
* Import AD dataset into BloodhoundAD to be parsed
* Use PlumHound to Report 


# Advisory and Initial Code Contribution
Help PlumHound grow and be a great tool for Blue and Purple Teams.  We've created the initial proof of concept and are committed to continuing the maturity of PlumHound to leverage the power of BloodHoundAD into continual security improvement processes.  Community involvement is what makes this industry great!  
* [Black Hills Information Security](https://www.blackhillsinfosec.com) | @[BHInfoSecurity](https://twitter.com/BHinfoSecurity) | [Discord](https://discord.gg/J4UJPgG)
* [Defensive Origins](https://www.defensiveorigins.com)   |  [@DefensiveOGs](https://twitter.com/DefensiveOGs) | [Git](https://github.com/DefensiveOrigins) 
* Kent Ickler  |  @[Krelkci](https://twitter.com/Krelkci) | [Git](https://github.com/Relkci)
* Jordan Drysdale |  [@Rev10D](https://twitter.com/Rev10D) | [Git](https://github.com/rev10d)


## License
[GNU GPL3](https://github.com/DefensiveOrigins/PlumHound/blob/master/LICENSE) 
