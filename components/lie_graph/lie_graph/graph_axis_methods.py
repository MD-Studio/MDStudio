# -*- coding: utf-8 -*-

"""
Graph axis methods

Functions for traversing and querying (sub)graph hierarchy with respect
to a root node. These functions are similar to the axis methods commonly found
in XML libraries.

All these functions accept a (sub)graph, a node id (nid) to query axis based
hierarchy for and a root nid relative to wich the hierarchy should be
defined.
"""

from itertools import combinations

from .graph_algorithms import dijkstra_shortest_path


def closest_to(graph, source, target):
    """
    Determine which of the target nodes are closest to the source node.

    :param source: source node id
    :type source:  int
    :param target: target node id's
    :type target:  list

    :rtype:        list
    """

    if source in target:
        target.remove(source)

    if not len(target):
        return [source]
    if len(target) == 1:
        return target

    shortest = {}
    for nid in sorted(target):
        path = dijkstra_shortest_path(graph._full_graph, source, nid)
        shortest[nid] = set(path)

    remove = []
    for comb in combinations(shortest.keys(), 2):
        if shortest[comb[0]].issubset(shortest[comb[1]]):
            remove.append(comb[1])

    return [n for n in shortest.keys() if n not in remove]


def node_ancestors(graph, nid, root, include_self=False):
    """
    Return the ancestors of the source node

    :param node:         source node to start search from
    :type node:          mixed
    :param include_self: include source nid in results
    :type include_self:  bool
    """

    anc = dijkstra_shortest_path(graph._full_graph, root, nid)

    if not include_self and anc[-1] == nid:
        anc.pop()

    return anc


def node_children(graph, nid, root, include_self=False):
    """
    Return the children of the source node.

    :param node:         source node to start search from
    :type node:          mixed
    :param include_self: include source nid in results
    :type include_self:  bool
    """

    # Children are all neighbors of the node except the parent
    p = node_parent(graph, nid, root)
    children = [n for n in node_neighbors(graph, nid) if not n == p]

    if include_self:
        children.insert(0, nid)

    return children


def node_descendants(graph, nid, root, include_self=False):
    """
    Return all descendants nodes to the source node

    :param node:         source node to start search from
    :type node:          mixed
    :param include_self: include source nid in results
    :type include_self:  bool
    """

    # Get nid child nodes to start descendants walk from
    # Add self to avoid backtracking during the walk
    start = node_children(graph, nid, root, include_self=True)

    def _walk(child_nid):
        ch = node_neighbors(graph, child_nid)
        for c in ch:
            if c not in start:
                start.append(c)
                _walk(c)

    # Start descendants walk from child nodes
    for child_nid in [i for i in start if not i == nid]:
        _walk(child_nid)

    if not include_self:
        start.remove(nid)

    return start


def node_neighbors(graph, nid):
    """
    Return de neighbor nodes of the node.

    ..  note:: if the current graph is a subgraph view (is_view == True) of
               the parent graph than only the neighbor nodes represented by
               the subgraph will be considered.

    :param graph: Graph to query
    :type graph:  Graph class instance
    :param node:  node to return neighbors for
    :type node:   lie_graph.graph_axis_class.GraphAxisMethods.nid
    """

    if graph.is_masked:
        nodes = set(graph.nodes.keys())
    else:
        nodes = set(graph._full_graph.nodes.keys())

    return sorted(nodes.intersection(set(graph.adjacency[nid])))


def node_parent(graph, nid, root):
    """
    Get the parent node of the source node relative to the graph root
    when following the shortest path (Dijkstra shortest path).

    :param node: node to define parent of
    :type node:  int

    :return:     parent node
    :rtype:      Graph object
    """

    shortest_path = dijkstra_shortest_path(graph._full_graph, root, nid)
    if len(shortest_path) > 1 and shortest_path[-1] == nid:
        return shortest_path[-2]
    return None

def node_all_parents(graph, nid, root):
    """
    Get all parent nodes to the source node relative to the graph root
    
    :param node: node to define parents of
    :type node:  int

    :return:     parent node nids
    :rtype:      :py:list
    """
    
    children = node_children(graph, nid, root)
    all_parents = [key for key,value in graph.adjacency().items() if 
        nid in value and not key in children]
        
    return all_parents

def node_siblings(graph, nid, root):
    """
    Get the siblings of the source node

    :param node: source node to start search from
    :type node:  mixed

    :return:     sibling node nids
    :rtype:      :py:list
    """

    # Siblings are all children of the nid parent except self.
    parent = node_parent(graph, nid, root)
    siblings = []
    if parent is not None:
        if graph.is_masked:
            siblings = [
                n for n in node_children(graph._full_graph, parent, graph.root)
                if not n == nid and n in graph.nodes]
        else:
            siblings = [n for n in node_children(
                graph._full_graph, parent, graph.root) if not n == nid]

    return siblings
