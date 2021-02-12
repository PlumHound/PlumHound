from py2neo import Graph, Path


def analyze_path(fneodb, fneouser, fneopass, path: Path):
    start_node = path.start_node['name']
    end_node = path.end_node['name']
    # This fonction is used when a start node and a and node is specified.
    query = """MATCH p=shortestpath((n {name: $snode})-[*1..]->(m {name: $enode}))
        UNWIND relationships(p) as relToOmit
        OPTIONAL MATCH path = shortestPath((n)-[*1..]->(m))
        WHERE none(rel in relationships(path) WHERE rel = relToOmit)
        WITH path, relToOmit
        WHERE path IS NULL
        RETURN startNode(relToOmit).name as snode, endNode(relToOmit).name as enode, type(relToOmit) as rel, id(relToOmit) as relId"""
    graph = Graph(fneodb, user=fneouser, password=fneopass)
    result = graph.run(query, snode=start_node, enode=end_node)
    if result:
        actionables = []
        while result.forward():
            actionables.append({
                'rel': result.current["rel"],
                'a': result.current["snode"],
                'b': result.current["enode"],
            })
            # print("Removing the relationship", result.current["rel"], "between", result.current["snode"], "and", result.current["enode"], "breaks the path!")
        nodes = [{'id': node['name']} for node in path.nodes]
        links = [{'source': rel.start_node['name'], 'target': rel.end_node['name']} for rel in path.relationships]
        return {
            'actionables': actionables,
            'nodes': nodes,
            'links': links,
        }
    else:
        # print("There is no path between startnode and endnode")
        return False


def get_paths(fneodb, fneouser, fneopass, startnode, endnode):
    # This function will get the shortest paths from StarNode and EndNode
    # First we initiate our graph
    graph = Graph(fneodb, user=fneouser, password=fneopass)
    # Test if we received a label or 2 nodes and build the query accordingly
    if startnode == "User" or startnode == "Group" or startnode == "Computer":
        nodetype = startnode
        query = 'MATCH p=ShortestPath((n:%s)-[*1..]->(m:Group)) WHERE m.name STARTS WITH "DOMAIN ADMINS@" AND n <> m RETURN p' % (nodetype)
    else:
        query = 'MATCH p=ShortestPath((n {name: "%s"})-[*1..]->(m {name: "%s"})) WHERE n <> m RETURN p' % (startnode, endnode)
    paths = graph.run(query)

    results = [analyze_path(fneodb, fneouser, fneopass, d['p']) for d in paths.data()]

    filtered_results = [result for result in results if result and len(result['actionables']) > 0]

    print('fr', filtered_results)

    return filtered_results


# TODO: Need a reasonable way to limit results
def find_busiest_path(fneodb, fneouser, fneopass, param):
    # This function counts how many principals have the same path
    # The goal is to find the path(s) which give the most users a path and focus on it to remediate
    graph = Graph(fneodb, user=fneouser, password=fneopass)
    if param.lower() == "all":
        query_shortpath = """MATCH p=allShortestPaths((n)-[*1..]->(m:Group)) where m.name starts with "DOMAIN ADMINS" and n<>m RETURN p"""
    else:
        query_shortpath = """MATCH p=ShortestPath((n)-[*1..]->(m:Group)) where m.name starts with "DOMAIN ADMINS" and n<>m RETURN p"""
    paths = graph.run(query_shortpath)
    path = paths.evaluate()
    # if path is None:
    #     print("---------------------------------------------------------------------")
    #     print("There is no ShortestPath")
    #     print("---------------------------------------------------------------------")
    ucount = []
    while path is not None:
        snode = path.start_node["name"]
        query_count_user = """match p=shortestpath((s)-[*1..]->(d:Group))
where s.name = "%s" and d.name starts with "DOMAIN ADMINS" and s<>d
unwind (NODES(p)) as pathNodes
match (pathNodes) where labels(pathNodes) = ["Base", "Group"]
with pathNodes as grp
match (grp)<-[:MemberOf*1..]-(u:User)
return count(distinct(u))""" % snode
        usercount = graph.run(query_count_user)
        nb_user = usercount.evaluate()
        result = [nb_user, snode]
        ucount.append(result)
        path = paths.evaluate()
    ucount.sort(reverse=True)
    print(ucount)
    return [{'count': count, 'name': name} for count, name in ucount]
