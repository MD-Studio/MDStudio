# -*- coding: utf-8 -*-

import pprint
import os
import logging as logger

from .graph import Graph


def coarse_type(n):

    if n.isdigit():
        return int(n)
    return n


def _nest_flattened_dict(graph_dict, sep='.'):
    """
    Convert a dictionary that has been flattened by the
    `_flatten_nested_dict` method to a nested representation

    :param graph_dict: dictionary to nest
    :type graph_dict:  dict
    :param sep:        concatenation seperator
    :type sep:         str

    :return:           nested dictionary
    :rtype:            dict
    """

    nested_dict = {}
    for key, value in sorted(graph_dict.items()):

        splitted = key.split(sep)
        if len(splitted) == 1:
            nested_dict[key] = value

        d = nested_dict
        for k in splitted[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]

        d[splitted[-1]] = value

    return nested_dict


def dict_to_graph(dictionary, graph, keystring='key', valuestring='value'):

    assert isinstance(dictionary, dict), TypeError("Default configuration needs to be a dictionary type, got: {0}".format(type(dictionary)))

    graph.node_data_tag = keystring
    rootnid = graph.add_node('config')
    graph.root = rootnid

    def _walk_dict(key, item, rootnid):

        nid = graph.add_node(key)
        graph.add_edge(rootnid, nid)

        if isinstance(item, dict):
            for k, v in sorted(item.items()):
                _walk_dict(k, v, nid)
        else:
            graph.nodes[nid][valuestring] = item

    for k, v in sorted(dictionary.items()):
        _walk_dict(k, v, rootnid)

    return graph


def read_tgf(tgf, edge_data_label='label'):
    """
    Read graph in Trivial Graph Format

    TGF format dictates that nodes to be listed in the file first
    with each node on a new line. A '#' character signals the end
    of the node list and the start of the edge list.

    Node and edge ID's can be integers, float or strings.
    They are mapped against the Graphs internal node ID (nid).
    If edges connect nodes that do not exist, an error is logged
    and the edge is skipped.

    :param tgf: TGF graph data.
    :type tgf: File, string, stream or URL
    :param edge_data_label: Graph edge metadata dictionary key to
           use for parsed edge labels. 'label' by default.
    :type edge_data_label: string
    :return: Graph object
    """

    with open(tgf) as tgf_file:

        nodes = True
        node_dict = {}

        # Initiate new empty graph
        graph = Graph()

        # Start parsing file lines. First extract nodes
        for line in tgf_file.readlines():

            line = line.strip()
            if len(line):

                # Reading '#' character means switching from node
                # definition to edges
                if line.startswith('#'):
                    nodes = False
                    continue

                # Coarse string to types
                line = [coarse_type(n) for n in line.split()]

                # Parse nodes
                if nodes:
                    if len(line) > 1:
                        attr = ' '.join([repr(e) for e in line[1:]])
                        nid = graph.add_node(line[0], tgf=attr)
                    else:
                        nid = graph.add_node(line[0])
                    node_dict[line[0]] = nid

                # Parse edges
                else:
                    e1 = node_dict[line[0]]
                    e2 = node_dict[line[1]]
                    for node in (e1, e2):
                        if node not in graph.nodes:
                            logger.error('Node {0} in edge {1}-{2} not in graph. Skipping edge'.format(node, e1, e2))
                            continue

                    attr = None
                    if len(line) > 2:
                        attr = {edge_data_label: ' '.join([str(e) for e in line[2:]])}
                    graph.add_edge(e1, e2, attr=attr)

    return graph


def write_graph(graph, path=os.path.join(os.getcwd(), 'graph.gpf'), pickle=False):
    """
    Export graph as Graph Python Format file

    GPF format is the modules own file format consisting out of a serialized
    or pickled nodes and edges dictionary.
    The format is feature rich wth good performance but is not portable.

    :param graph:  Graph object to export
    :type graph:  Graph instance
    :param path:   File path to write to
    :type path:   path as string
    :param pickle: export graph as pickled GPF format
    :type pickle: bool
    :return: Graph instance
    """

    # Export graph as pickled Graph Python Format
    if pickle:

        import pickle
        pickle_dict = {}
        pickle_dict['nodes'] = graph.nodes.dict()
        pickle_dict['edges'] = graph.edges.dict()

        with open(path, "wb") as output:
            pickle.dump(pickle_dict, output)

        logger.info('Graph exported in pickled GPF format to file: {0}'.format(path))

    # Export graph as serialized Graph Python Format
    else:

        pp = pprint.PrettyPrinter(indent=2)
        with open(path, 'w') as output:

            # Export nodes as dictionary
            output.write('nodes = {0}\n'.format(pp.pformat(graph.nodes.dict())))

            # Export edges as dictionary
            output.write('edges = {0}\n'.format(pp.pformat(graph.edges.dict())))

        logger.info('Graph exported in GPF format to file: {0}'.format(path))


def read_graph(graph_file, graph=None, pickle=False):
    """
    Import graph from Graph Python Format file

    GPF format is the modules own file format consisting out of a serialized
    or pickled nodes and edges dictionary.
    The format is feature rich wth good performance but is not portable.

    :param path:   File path to read from
    :type path:   path as string
    :param graph:  Graph object to import to or Graph by default
    :type graph:  Graph instance
    :param pickle: Import graph as pickled GPF format
    :type pickle: bool
    :return: Graph instance
    """

    if not graph:
        graph = Graph()

    # Import graph from pickled Graph Python Format
    if pickle:
        import pickle

        with open(graph_file, mode='rb') as graph_file:
            pickle_dict = pickle.load(graph_file)

            if 'nodes' in pickle_dict and 'edges' in pickle_dict:
                graph.nodes._storage = pickle_dict['nodes']
                graph.edges._storage = pickle_dict['edges']

            adjacency = dict([(n, []) for n in pickle_dict['nodes']])
            for edge in pickle_dict['edges']:
                adjacency[edge[0]].append(edge[1])

            graph.adjacency._storage = adjacency

        logger.info('Graph imported from pickled GPF format file: {0}'.format(graph_file.name))

    # Import graph from serialized Graph Python Format
    else:
        with open(graph_file) as f:
            code = compile(f.read(), "GPF_file", 'exec')
            exec(code, global_vars, local_vars)

    return graph
