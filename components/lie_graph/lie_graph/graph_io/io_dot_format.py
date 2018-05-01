# -*- coding: utf-8 -*-

"""
file: io_dict_format.py

Functions for exporting and importing graphs to and from graph description
language (DOT) format
"""

import sys
import json

if sys.version_info[0] < 3:
    import StringIO
else:
    from io import StringIO

from lie_graph import __module__, __version__


def write_dot(graph, node_key_tag=None, edge_key_tag=None, graph_name='graph', dot_directives={}):
    """
    DOT graphs are either directional (digraph) or undirectional, mixed mode
    is not supported.

    Basic types for node and edge attributes are supported.

    :param graph:          Graph object to export
    :type graph:           :lie_graph:Graph
    :param node_key_tag:   node data key
    :type node_key_tag:    :py:str
    :param edge_key_tag:   edge data key
    :type edge_key_tag:    :py:str
    :param graph_name:     graph name to include
    :type graph_name:      :py:str
    :param dot_directives: special DOT format rendering directives
    :type dot_directives:  :py:dict

    :return:               DOT graph representation
    :rtype:                :py:str
    """

    # Define node and edge data tags to export
    node_key_tag = node_key_tag or graph.node_key_tag
    edge_key_tag = edge_key_tag or graph.edge_key_tag
    indent = ' ' * 4
    link = '->' if graph.is_directed else '--'
    allowed_attr_types = (int, float, bool, str, unicode)

    # Create empty file buffer
    string_buffer = StringIO.StringIO()

    # Write header comment and graph container
    string_buffer.write('//Created by {0} version {1}\n'.format(__module__, __version__))
    string_buffer.write('{0} "{1}" {2}\n'.format('digraph' if graph.is_directed else 'graph', graph_name, '{'))

    # Write special DOT directives
    for directive, value in dot_directives.items():
        string_buffer.write('{0}{1}={2}\n'.format(indent, directive, value))

    # Export nodes
    string_buffer.write('{0}//nodes\n'.format(indent))
    for node in graph.iternodes():
        attr = ['{0}={1}'.format(k, json.dumps(v)) for k,v in node.nodes[node.nid].items() if
                isinstance(v, allowed_attr_types) and not k.startswith('$')]
        if attr:
            string_buffer.write('{0}{1} [{2}];\n'.format(indent, node.nid, ','.join(attr)))

    # Export adjacency
    string_buffer.write('{0}//edges\n'.format(indent))
    done = []
    for node, adj in graph.adjacency.items():
        for a in adj:
            edges = [(node, a), (a, node)]

            if all([e not in done for e in edges]):
                attr = {}
                for edge in edges:
                   attr.update(graph.edges.get(edge, {}))
                attr = ['{0}={1}'.format(k, json.dumps(v)) for k, v in attr.items() if
                        isinstance(v, allowed_attr_types) and not k.startswith('$')]

                if attr:
                    string_buffer.write('{0}{1} {2} {3} [{4}];\n'.format(indent, node, link, a, ','.join(attr)))
                else:
                    string_buffer.write('{0}{1} {2} {3};\n'.format(indent, node, link, a))

            done.extend(edges)

    # Closing curly brace
    string_buffer.write('}\n')

    # Reset buffer cursor
    string_buffer.seek(0)
    return string_buffer.read()