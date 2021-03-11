from py2neo import Graph, Path
import re


# honestly couldn't figure out how to get the name of a relationship.
# I thought it should just be this:
# https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.graph.Relationship.type
# but couldn't get it to work so here we are.
def get_rel_name(rel):
    match = re.search(r"\[:(\w+) \{.*}\]", rel.type(rel).__name__)
    if not match:
        raise Exception(f'Couldn\'t parse the relationship "{rel.type(rel).__name__}"')
    return match.group(1)


def analyze_path(fneodb, fneouser, fneopass, path: Path):
    return {
        "links": [{'source': rel.start_node['name'], 'target': rel.end_node['name'], 'relationship': get_rel_name(rel)} for rel in path.relationships],
        "nodes": [{'id': node['name']} for node in path.nodes],
    }


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

    # sorts results by number of nodes
    results.sort(key=lambda r: len(r['nodes']), reverse=True)

    # Remove paths from results that are a subpath of another
    # destination is the same so we can start with the longest path
    # and only add paths that start at an unvisited node
    filtered_results = []

    visited = set()
    for result in results:
        if result['nodes'][0]['id'] not in visited:
            filtered_results.append(result)
            for node in result['nodes']:
                visited.add(node['id'])

    results = filtered_results

    # inefficient, but I doubt (hope) there are no domains big enough for this to be an issue
    most_used = []
    for result in results:
        for link in result['links']:
            found = None
            for test in most_used:
                if test['target'] == link['target'] and test['relationship'] == link['relationship']:
                    found = test
                    break
            if found is None:
                most_used.append({
                    'target': link['target'],
                    'relationship': link['relationship'],
                    'count': 1,
                })
            else:
                test['count'] += 1

    # sorts stats by number of uses
    most_used.sort(key=lambda d: d['count'], reverse=True)

    return {
        "graphs": results,
        "mostUsedRelationships": most_used
    }


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
    # print(ucount)
    return [{'count': count, 'name': name} for count, name in ucount]
