from py2neo import Graph, Node, Relationship

#######################################################
#
# Change the variable below to reflect your environment
#
#######################################################

neodb="bolt://localhost:7687"
neouser="neo4j"
neopass="password"

# End of config

def analyzepath(fneodb,fneouser,fneopass,startnode,endnode):
    # This fonction is used when a start node and a and node is specified.
    query="""MATCH p=shortestpath((n {name: $snode})-[*1..]->(m {name: $enode}))
        UNWIND relationships(p) as relToOmit
        OPTIONAL MATCH path = shortestPath((n)-[*1..]->(m))
        RETURN startNode(relToOmit).name as snode, endNode(relToOmit).name as enode, type(relToOmit) as rel, id(relToOmit) as relId"""
    graph = Graph(fneodb,user=fneouser,password=fneopass)
    result=graph.run(query,snode=startnode,enode=endnode) 
    if result:
        while result.forward():
            print("Removing the relationship", result.current["rel"] ,"between", result.current["snode"] ,"and", result.current["enode"] ,"breaks the path!")
    else:
        print("There is no path between startnode and endnode")


def getpaths(fneodb,fneouser,fneopass,startnode,endnode):
    # This function will get the shortest paths from StarNode and EndNode
    # First we initiate our graph
    graph = Graph(fneodb,user=fneouser,password=fneopass)
    # Test if we received a label or 2 nodes and build the query accordingly
    if startnode == "AZUser" or startnode == "AZGroup" or startnode == "AZDevice" or startnode == "AZServicePrincipal" or startnode == "AZApp":
        query='MATCH p=ShortestPath((n:%s)-[*1..]->(m:AZRole)) WHERE m.name STARTS WITH "%s@" AND n <> m RETURN p' % (startnode, endnode)
    else:
        query='MATCH p=ShortestPath((n {name: "%s"})-[*1..]->(m {name: "%s"})) WHERE n <> m RETURN p' % (startnode,endnode)
    paths=graph.run(query)
    # Extract the starting & ending node of each paths and send them to be analyzed
    path=paths.evaluate()
    if path == None:
        print ("---------------------------------------------------------------------")
        print("There is no path between", startnode,"and", endnode)
        print ("---------------------------------------------------------------------")
    while path != None:
        snode=path.start_node["name"]
        enode=path.end_node["name"]
        print ("---------------------------------------------------------------------")
        print ("Analyzing paths between", snode, "and", enode)
        print ("---------------------------------------------------------------------")
        analyzepath(fneodb,fneouser,fneopass,snode,enode)
        path=paths.evaluate()
        pass

# Unimplemented

# def find_busiest_path(fneodb,fneouser,fneopass,param,number):
#     # This function counts how many principals have the same path
#     # The goal is to find the path(s) which give the most users a path and focus on it to remediate
#     graph = Graph(fneodb,user=fneouser,password=fneopass)
#     if param.lower() == "all":
#         query_shortpath="""MATCH p=allShortestPaths((n)-[*1..]->(m:AZRole)) where m.name starts with "GLOBAL ADMIN" and n<>m RETURN p"""
#     else: 
#         query_shortpath="""MATCH p=ShortestPath((n)-[*1..]->(m:AZRole)) where m.name starts with "GLOBAL ADMIN" and n<>m RETURN p"""
#     paths=graph.run(query_shortpath)
#     path=paths.evaluate()
#     if path == None:
#         print ("---------------------------------------------------------------------")
#         print("There is no ShortestPath")
#         print ("---------------------------------------------------------------------")
#     x=0
#     ucount=[]
#     while path != None:
#         snode=path.start_node["name"]
#         query_count_user="""match p=shortestpath((s)-[*1..]->(d:AZRole))
# where s.name = "%s" and d.name starts with "GLOBAL ADMIN" and s<>d
# unwind (NODES(p)) as pathNodes
# match (pathNodes) where labels(pathNodes) = ["AZBase", "AZRole"]
# with pathNodes as grp
# match (grp)<-[:MemberOf*1..]-(u:AZUser)
# return count(distinct(u))
#         """ % snode
#         usercount=graph.run(query_count_user)
#         nb_user=usercount.evaluate()
#         result=[nb_user, snode]
#         ucount.append(result)
#         x=x+1
#         path=paths.evaluate()
#     ucount.sort(reverse=True)
#     i=0
#     nb_paths=int(number)
#     while i<nb_paths:
#         try:
#             print(ucount[i])
#             i=i+1
#         except Exception as e: # If there are less results than specified.
#             i=i+1
#     return (ucount)


def main():
    # Nothing here as this code should be used with Plumhound : https://github.com/PlumHound/PlumHound
    x=0

if __name__ == "__main__":
    main()
