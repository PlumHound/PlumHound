#!/usr/bin/env python
# -*- coding: utf8 -*-
# PlumHound (phTaskzipper.py) - Create Zip of tasks
# https://github.com/PlumHound/PlumHound 
# License GNU GPL3

#Python Libraries
import pydot

#Plumhound Modules
from lib.phLoggy import Loggy as Loggy

def ph_visualize(verbose,cypherresult, OutPathFile, Outpath):
    Loggy(verbose,900, "------ENTER: graph visualizer-----")
    graph = pydot.Dot(graph_type='digraph')
    # Add nodes and edges to the Pydot graph
    for record in result:
        d1_name = record["d1"]["name"]
        d2_name = record["d2"]["name"]
        # Add nodes
        node1 = pydot.Node(d1_name)
        node2 = pydot.Node(d2_name)
        if node1 not in graph.get_nodes():
            graph.add_node(node1)
        if node2 not in graph.get_nodes():
            graph.add_node(node2)
        # Add edge
        edge = pydot.Edge(d1_name, d2_name)
        graph.add_edge(edge)
        
    graph.write_png(Outpath+OutPathFile)

    Loggy(verbose,900, "------EXIT:  graph visualizer-----")
    return True


