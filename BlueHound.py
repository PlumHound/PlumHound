from py2neo import Graph, Node, Relationship

#######################################################
#
# Change the variable below to reflect your environment
#
#######################################################

neodb="bolt://localhost:7687"
neouser="neo4j"
neopass="neo4jj"

# End of config

def analyzepath(fneodb,fneouser,fneopass,startnode,endnode):
	# This fonction is used when a start node and a and node is specified.
	query="""MATCH p=shortestpath((n {name: $snode})-[*1..]->(m {name: $enode}))
		UNWIND relationships(p) as relToOmit
		OPTIONAL MATCH path = shortestPath((n)-[*1..]->(m))
		WHERE none(rel in relationships(path) WHERE rel = relToOmit)
		WITH path, relToOmit
		WHERE path IS NULL
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
	if startnode == "User" or startnode == "Group" or startnode == "Computer":
		nodetype=startnode
		query='MATCH p=ShortestPath((n:%s)-[*1..]->(m:Group)) WHERE m.name STARTS WITH "DOMAIN ADMINS@" AND n <> m RETURN p' % (nodetype)
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


def main():
	snode=input("Enter Starting Node Name ex: <\"BOB SMITH@EXAMPLE.COM\"> : ").upper() 	
	enode=input("Enter Starting Node Name ex: <\"DOMAIN ADMINS@EXAMPLE.com\"> : ").upper()
	if snode == "USER":
		snode="User"
		endnode=""
	elif snode == "GROUP":
		snode="Group"
		enode=""
	elif snode == "COMPUTER":
		snode="Computer"
		enode=""
	else:
		snode=snode.upper()
		enode=snode.upper()
	getpaths(neodb,neouser,neopass,snode,enode)

if __name__ == "__main__":
	main()
