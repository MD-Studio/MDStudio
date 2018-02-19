# -*- coding: utf-8 -*-

import logging as logger

from lie_graph.graph_helpers import GraphException
from lie_graph.graph import Graph
from lie_graph.graph_axis.graph_axis_class import GraphAxis
from lie_graph.graph_axis.graph_axis_methods import closest_to
from lie_graph.graph_algorithms import dijkstra_shortest_path
from lie_graph.graph_io.io_helpers import _nest_flattened_dict


def read_dict(dictionary, graph=None, node_data_tag=None, edge_data_tag=None, valuestring='value'):
    """
    Parse (hierarchical) dictionary data structure to a graph

    :param dictionary:      dictionary
    :type dictionary:       :py:dict
    :param graph:           Graph object to import dictionary data in
    :type graph:            :lie_graph:Graph
    :param node_data_tag:   Data key to use for parsed node labels.
    :type node_data_tag:    :py:str
    :param edge_data_tag:   Data key to use for parsed edge labels.
    :type edge_data_tag:    :py:str

    :return:                Graph object
    :rtype:                 :lie_graph:Graph
    """

    assert isinstance(dictionary, dict), \
        TypeError("Requires dictionary, got: {0}".format(type(dictionary)))

    if not isinstance(graph, Graph):
        graph = GraphAxis()

    # Define node/edge data labels
    if node_data_tag:
        graph.node_data_tag = node_data_tag
    if edge_data_tag:
        graph.edge_data_tag = edge_data_tag

    rootnid = graph.add_node('root')
    graph.root = rootnid

    def _walk_dict(key, item, rootnid):

        nid = graph.add_node(key)
        graph.add_edge(rootnid, nid)

        if isinstance(item, dict):
            for k, v in sorted(item.items()):
                _walk_dict(k, v, nid)
        else:
            node = graph.getnodes(nid)
            node.set(valuestring, item)

    for k, v in sorted(dictionary.items()):
        _walk_dict(k, v, rootnid)

    return graph


def write_dict(graph, keystring='key', valuestring=None, nested=True, sep='.',
                  path_method=dijkstra_shortest_path, default=None):
    """
    Export a graph to a (nested) dictionary

    Convert graph representation of the dictionary tree into a dictionary
    using a nested or flattened representation of the dictionary hierarchy.

    In a flattened representation, the keys are concatenated using the `sep`
    separator.
    Dictionary keys and values are obtained from the node attributes using
    `keystring` and `valuestring` that are set to graph node_key_tag and
    node_data_tag by default.

    The hierarchy in the dictionary is determined by calculating the
    shortest path (dijkstra_shortest_path) from the current root node
    to the leaf nodes (leaves method) in the (sub)graph

    :param nested:      return a nested or flattened dictionary
    :type nested:       bool
    :param sep:         key separator used in flattening the dictionary
    :type sep:          str
    :param keystring:   key used to identify dictionary 'key' in node
                        attributes
    :type keystring:    str
    :param valuestring: key used to identify dictionary 'value' in node
                        attributes
    :type valuestring:  str
    :param default:     value to use when node value was not found using
                        valuestring.
    :type default:      mixed
    :param path_method: method used to calculate shortest path between
                        root node and leaf node
    :type path_method:  method
    :rtype:             dict

    TODO: get path between nodes closest to root and leaves using closest_to
          method is potentially slow for large graphs.
    """

    # Graph should inherit from Graph baseclass
    if not isinstance(graph, Graph):
        raise GraphException('Graph {0} not a valid "Graph" object'.format(type(graph)))

    # No nodes, return empty dict
    if not len(graph.nodes):
        return {}

    # Resolve node dictionary attributes for value
    valuestring = valuestring or graph.node_data_tag

    # Determine rootnode relative to which hierarchy is resolved
    if graph.root is None:
        rootnodes = [min(graph.nodes.keys())]
        logger.debug('No root node defined, set to node with _id: {0}'.format(rootnodes[0]))

    if graph.root in graph.nodes:
        rootnodes = [graph.root]
    else:
        rootnodes = closest_to(graph, graph.root, list(graph.nodes.keys()))

    # Construct the flattened dictionary first
    graph_dict = {}
    for nid in rootnodes:
        subgraph = graph.descendants(nid, include_self=True)
        leaves = subgraph.leaves(return_nids=True)

        for leave in leaves:
            path = path_method(graph._full_graph, nid, leave)
            flattened = sep.join([str(graph._full_graph.nodes[p][keystring]) for p in path])
            graph_dict[flattened] = graph.getnodes(leave).get(valuestring, default=default)

    # Flatten the dictionary if needed
    if nested:
        graph_dict = _nest_flattened_dict(graph_dict, sep=sep)

    return graph_dict
