
![PlumHound](https://raw.githubusercontent.com/DefensiveOrigins/PlumHound/master/docs/images/Plum3.jpg)

# PlumHound - BloodHoundAD Report Engine for Security Teams
BloodhoundAD Reporting Engine for Blue and Purple Teams.

Released as Proof of Concept for Blue and Purple teams to more effectively use BloodHoundAD in continual security life-cycles by utilizing the BloodHoundAD pathfinding engine to identify Active Directory security vulnerabilities resulting from business operations, procedures, policies and legacy service operations.

PlumHound operates by wrapping BloodHoundAD's powerhouse graphical Neo4JS backend cypher queries into operations consumable reports.  Analyzing the output of PlumHound can steer security teams in identifying and hardening common Active Directory configuration vulnerabilities and oversights.

## Release and call to Action
The initial PlumHound code was released on May 14th, 2020 during a Black Hills Information Security webcast, A Blue Teams Perspective on Red Team Tools.  The webcast was recorded and is available on YouTuve here[Link TBA]. 

## Background
A client of ours working on hardening their Active Directory infrastructure asked us about vulnerabilities that can be found by using BloodHound.  They had heard of the effectiveness of BloodHoundAD in Red-Team's hands and was told that BloodHound would identify all types of security mis-alignments and mis-configurations in their Active Directory environment.  We helped them through analysis of their BloodHound dataset and it became quickly evident that BloodHoundAD's pathfinding graphical database was not designed for the fast-passed analytical security team accustom to reading reports and action items.  

In fact, one of our cypher queries determined that 96% of their 3000 users had a path to Domain Admin with an average of just 4 steps.  However, that graphical query rendered over 10,000 paths to Domain Admin.  Finding the actual cause of the short-paths to DA wasn't as easy as just loading data into BloodHound or putting Cobalt Strike on Auto-Pilot with BloodHound Navigation.  
Hence, PlumHound was created out of a need to retrieve consumable data from BloodHoundAD's pathfinding engine.  Data that could yield itself to inferring actionable work for security teams to harden their environments.

## Same Reports


## PlumHound Syntax
```plaintext
usage: PlumHound.py [-h] [-s, --server S, __SERVER] [-u, --Username U, __USERNAME] [-p, --Password P, __PASSWORD] [--easy EASY]
                    [-x --TaskFile X __TASKFILE] [-c, --QuerySingle C, __QUERYSINGLE] [-t, --title T, __TITLE] [--of, --OutFile OF, __OUTFILE]
                    [--op, --OutPath OP, __OUTPATH] [--of, --OutFormat {stdout,grep,HTML,CSV}] [--HTMLHeader HTMLHEADER] [--HTMLFooter HTMLFOOTER]
                    [--HTMLCSS HTMLCSS] [-v, --Verbose V, __VERBOSE]

BloodHound Wrapper for Purple Teams

optional arguments:
  -h, --help            show this help message and exit

DATABASE:
  -s, --server S, __SERVER
                        Neo4J Server
  -u, --Username U, __USERNAME
                        Neo4J Database Useranme
  -p, --Password P, __PASSWORD
                        Neo4J Database Password

TASKS:
  Task Selection

  --easy EASY           [DEFAULT] Use a sample Cypher Query Exported to STDOUT
  -x --TaskFile X __TASKFILE
                        PlumHound Plan of Cypher Queries
  -c, --QuerySingle C, __QUERYSINGLE
                        Specify a Single cypher Query

SINGLE QUERY:
  Extended Options for Single Cypher Query Wrapping

  -t, --title T, __TITLE
                        Report Title for Single Query [HTML,CSV,Latex]

OUTPUT:
  Output Options

  --of, --OutFile OF, __OUTFILE
                        Specify a Single Cypher Query
  --op, --OutPath OP, __OUTPATH
                        Specify an Output Path for Reports
  --of, --OutFormat {stdout,grep,HTML,CSV}
                        Specify the type of output

HTML:
  Options for HTML Output

  --HTMLHeader HTMLHEADER
                        HTML Header (file) of Report
  --HTMLFooter HTMLFOOTER
                        HTML Footer (file) of Report
  --HTMLCSS HTMLCSS     Specify a CSS template for HTML Output

VERBOSESet verbosity:
  -v, --Verbose V, __VERBOSE
                        Verbosity 0-1000, 0 = quiet
```


## Installation Requirements (python 3.7/3.8)
* apt-get install python3.8
* pip3 install -r requirements.txt


## Environment Setup Instructions
* Install Neo4JS
* Install BloodhoundAD
* Import AD dataset into BloodhoundAD to be parsed
* Use PlumHound to Report 

## TaskList Files Syntax
The PlumHound Repo includes a sample TaskList that exports some basic BloodHoundAD Cypher queries to an HTML Report.  The included tasks\Default.tasks sample shows the basic syntax of the TaskList files.  The TaskList Files allow PlumHound to be fully scripted with batch jobs after the SharpHound dataset has been imported not BloodHoundAD on Neo4js.

### TaskList File Syntax

```plaintext
["Report Title","[Output-Format]","[Output-File]","[CypherQuery]"]
```
### TaskList Sample: default.tasks
The default.tasks file includes multiple tasks that instruct PlumHound to create reports using the specified "HTML" output format, output filename, and specific BloodHoundAD Neo4JS Cypher Query. 
```plaintext
["Domain Users HTML","HTML","DomainUsers.html","MATCH (n:User) RETURN n.name, n.displayname, n.description, n.title, n.pwdneverexpires, n.passwordnotreqd, n.sensitive, n.admincount, n.serviceprincipalnames"]
["Keroastable Users","HTML","Keroastable_Users.html","MATCH (n:User) WHERE n.hasspn=true RETURN n.name, n.displayname,n.description, n.title, n.pwdneverexpires, n.passwordnotreqd, n.sensitive, n.admincount, n.serviceprincipalnames"]
["RDPable Servers","HTML","Workstations_RDP.html","match p=(g:Group)-[:CanRDP]->(c:Computer) where  g.objectid ENDS WITH \'-513\'  AND c.operatingsystem CONTAINS \'Server\' return c.namep"]
["Unconstrained Delegation Computers","HTML","Workstations_UnconstrainedDelegation.html","MATCH (c:Computer) Where c.unconstraineddelegation=true return c.name, c.description, c.serviceprincipalnames, c.haslaps"]
["GPOs","HTML","GPOs.html","Match (n:GPO) return n.name, n.highvalue,n.gcpath"]
["Admin Groups","HTML","AdminGroups.html","Match (n:Group) WHERE n.name CONTAINS \'ADMIN\' return n.name, n.highvalue, n.description, n.admincount"]
["Shortest Path to DA","HTML","ShortestPathDA.html","MATCH (n:Computer),(m:Group {name:'DOMAIN ADMINS@DOMAIN.GR'}),p=shortestPath((n)-[r:MemberOf|HasSession|AdminTo|AllExtendedRights|AddMember|ForceChangePassword|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|CanRDP|ExecuteDCOM|AllowedToDelegate|ReadLAPSPassword|Contains|GpLink|AddAllowedToAct|AllowedToAct*1..]->(m)) RETURN p"]
["RDPable Groups","HTML","RDPableGroups.html","MATCH p=(m:Group)-[r:CanRDP]->(n:Computer) RETURN m.name, n.name ORDER BY m.name"]
["PasswordResetter Groups","HTML","Groups_CanResetPasswords.html","MATCH p=(m:Group)-[r:ForceChangePassword]->(n:User) RETURN m.name, n.name ORDER BY m.name"]
["LocalAdminGroups","HTML","LocalAdmin_Groups.html","MATCH p=(m:Group)-[r:AdminTo]->(n:Computer) RETURN m.name, n.name ORDER BY m.name"]
["LocalAdminGroups","HTML","LocalAdmin_Users.html","MATCH p=(m:User)-[r:AdminTo]->(n:Computer) RETURN m.name, n.name ORDER BY m.name"]
["DA Sessions","HTML","DA_Sessions.html","MATCH (n:User)-[:MemberOf]->(g:Group) WHERE g.objectid ENDS WITH \'-512\' MATCH p = (c:Computer)-[:HasSession]->(n) return g.name, c.name"]
["Keroastable Most Priv","HTML","Keroastable_Users_MostPriv.html","MATCH (u:User {hasspn:true}) OPTIONAL MATCH (u)-[:AdminTo]->(c1:Computer) OPTIONAL MATCH (u)-[:MemberOf*1..]->(:Group)-[:AdminTo]->(c2:Computer) WITH u,COLLECT(c1) + COLLECT(c2) AS tempVar UNWIND tempVar AS comps RETURN u.name,COUNT(DISTINCT(comps)) ORDER BY COUNT(DISTINCT(comps)) DESC"]
["OUs By Computer Member Count","HTML","OUs_Count.html","MATCH (o:OU)-[:Contains]->(c:Computer) RETURN o.name,o.guid,COUNT(c) ORDER BY COUNT(c) DESC"]
["Permissions for Everyone and Authenticated Users","HTML","Permissions_Everyone.html","MATCH p=(m:Group)-[r:AddMember|AdminTo|AllExtendedRights|AllowedToDelegate|CanRDP|Contains|ExecuteDCOM|ForceChangePassword|GenericAll|GenericWrite|GetChanges|GetChangesAll|HasSession|Owns|ReadLAPSPassword|SQLAdmin|TrustedBy|WriteDACL|WriteOwner|AddAllowedToAct|AllowedToAct]->(t) WHERE m.objectsid ENDS WITH \'-513\' OR m.objectsid ENDS WITH \'-515\' OR m.objectsid ENDS WITH \'S-1-5-11\' OR m.objectsid ENDS WITH \'S-1-1-0\' RETURN m.name,TYPE(r),t.name,t.enabled"]
["Most Admin Priviledged Groups","HTML","Groups_MostAdminPriviledged.html","MATCH (g:Group) OPTIONAL MATCH (g)-[:AdminTo]->(c1:Computer) OPTIONAL MATCH (g)-[:MemberOf*1..]->(:Group)-[:AdminTo]->(c2:Computer) WITH g, COLLECT(c1) + COLLECT(c2) AS tempVar UNWIND tempVar AS computers RETURN g.name AS GroupName,COUNT(DISTINCT(computers)) AS AdminRightCount ORDER BY AdminRightCount DESC"]
["Computers with Descriptions","HTML","Computers_WithDescriptions.html","MATCH (c:Computer) WHERE c.description IS NOT NULL RETURN c.name,c.description"]
["User No Kerb Needed","HTML","Users_NoKerbReq.html","MATCH (n:User {dontreqpreauth: true}) RETURN n.name, n.displayname, n.description, n.title, n.pwdneverexpires, n.passwordnotreqd, n.sensitive, n.admincount, n.serviceprincipalnames"]
["Users Computer Direct Admin Count","HTML","Users_Count_DirectAdminComputers.html","MATCH (u:User)-[:AdminTo]->(c:Computer) RETURN count(DISTINCT(c.name)) AS COMPUTER, u.name AS USER ORDER BY count(DISTINCT(c.name)) DESC"]
["Users Computer InDirect Admin Count","HTML","Users_Count_InDirectAdminComputers.html","MATCH (u:User)-[:AdminTo]->(c:Computer) RETURN count(DISTINCT(c.name)) AS COMPUTER, u.name AS USER ORDER BY count(DISTINCT(c.name)) DESC"]
["NeverActive Active Users","HTML","Users_NeverActive_Enabled.html","MATCH (n:User) WHERE n.lastlogontimestamp=-1.0 AND n.enabled=TRUE RETURN n.name ORDER BY n.name"]
["Users GPOs Access Weirdness","HTML","Users_GPO_CheckACL.html","MATCH p=(u:User)-[r:AllExtendedRights|GenericAll|GenericWrite|Owns|WriteDacl|WriteOwner|GpLink*1..]->(g:GPO) RETURN p LIMIT 25"]"]

```

## Hat-Tips
* [Hausec's Cypher Query CheatSheet](https://hausec.com/2019/09/09/bloodhound-cypher-cheatsheet/)  gave us a headstart on some decent pathfinding cypher queries.  | [Git](https://github.com/hausec)
* [SadProcessor's Blue Hands on BloodHound](https://github.com/SadProcessor/WatchDog) gave us a detailed primer on BloodHoundAD's ability to lead a BlueTeam to water. | [Git](https://github.com/SadProcessor).
* Additional work by SadProcessor with [Cypher Dog 3.0](https://github.com/SadProcessor/CypherDog) shows similar POC via utilizing BloodHoundAD's Cypher Queries with a RestAPI endpoint via PowerShell.  PlumHound operates similarly however written in python and designed for stringing multiple queries into consumable reports designed to infer actionable items. 
* [BloodHoundAD](https://github.com/BloodHoundAD/BloodHound): We wouldn't be talking about this at all if it weren't for the original BloodHoundAD work.  BloodHound is developed by @_wald0, @CptJesus, and @harmj0y.






## Advisory and Initial Code Contribution
Help PlumHound grow and be a great tool for Blue and Purple Teams.  We've created the initial proof of concept and are committed to continuing the maturity of PlumHound to leverage the power of BloodHoundAD into continual security improvement processes.  Community involvement is what makes this industry great!  
* [Black Hills Information Security](https://www.blackhillsinfosec.com) | @[BHInfoSecurity](https://twitter.com/BHinfoSecurity) | [Discord](https://discord.gg/J4UJPgG)
* [Defensive Origins](https://www.defensiveorigins.com)   |  [@DefensoveOGs](https://twitter.com/DefensiveOGs) | [Git](https://github.com/DefensiveOrigins) 
* Kent Ickler  |  @[Krelkci](https://twitter.com/Krelkci) | [Git](https://github.com/Relkci)
* Jordan Drysdale |  [@Rev10D](https://twitter.com/Rev10D) | [Git](https://github.com/rev10d)


## License
[GNU GPL3](https://github.com/DefensiveOrigins/PlumHound/blob/master/LICENSE) 