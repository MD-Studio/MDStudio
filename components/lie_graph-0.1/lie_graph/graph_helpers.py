# -*- coding: utf-8 -*-

import os
import StringIO

def _adjacency_to_edges(nodes, adjacency, node_source):
    """
    Construct edges for nodes based on adjacency.
    
    Edges are created for every node in `nodes` based on the neighbors of
    the node in adjacency if the neighbor node is also in `node_source`.
    The source of adjacency information would normally be self.graph and
    self.nodes for `node_source`. However, `node_source may` also equal
    `nodes` to return edges for the isolated graph.
    
    :param nodes:       nodes to return edges for
    :type nodes:        list
    :param adjacency:   node adjacency (self.graph)
    :type adjacency:    dict
    :param node_source: other nodes to consider when creating edges
    :type node_source:  list
    """
    
    edges = []
    for node in nodes:
        edges.extend([tuple([node,e]) for e in adjacency[node] if e in node_source])
    
    return edges

def _edge_list_to_adjacency(edges):
    """
    Create adjacency dictionary based on a list of edges
    
    :param edges: edges to create adjacency for
    :type edges:  list
    """
    
    adjacency = dict([(n,[]) for n in _edge_list_to_nodes(edges)])
    for edge in edges:
        adjacency[edge[0]].append(edge[1])
    
    return adjacency

def _edge_list_to_nodes(edges):
    """
    Create a list of nodes from a list of edges
    
    :param edges: edges to create nodes for
    :type edges:  list
    """
    
    return list(set(sum(edges, ())))

def _make_edges(nodes, directed=True):
    """
    Create an edge tuple from two nodes either directed
    (first to second) or undirected (two edges, both ways).
    
    :param nodes:    nodes to create edges for
    :type nodes:     list or tuple
    :param directed: greate directed edge or not
    :type directed:  bool
    """
    
    edges = [tuple(nodes)]
    if not directed:
        edges.append(nodes[::-1])
    
    return edges
      
class GraphException(Exception):
    """
    Graph Exception class.
    Logs the exception as critical before raising.
    """
    
    def __init___(self, message='', *args,**kwargs):
        logger.critical(message)
        Exception.__init__(self, *args,**kwargs)