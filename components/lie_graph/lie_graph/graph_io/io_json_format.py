# -*- coding: utf-8 -*-

"""
file: io_json_format.py

Functions for exporting and importing graphs in structured JSON format
"""

import logging
import json

from lie_graph.graph_io.io_helpers import open_anything
from lie_graph.graph_io.io_dict_format import read_dict, write_dict


def read_json(json_file, graph=None, node_key_tag=None, edge_key_tag=None, valuestring='value'):
    """
    Parse (hierarchical) JSON data structure to a graph

    :param json_file:      json data to parse
    :type json_file:       File, string, stream or URL
    :param graph:          Graph object to import dictionary data in
    :type graph:           :lie_graph:Graph
    :param node_key_tag:   Data key to use for parsed node labels.
    :type node_key_tag:    :py:str
    :param edge_key_tag:   Data key to use for parsed edge labels.
    :type edge_key_tag:    :py:str
    :param valuestring:    Data key to use for dictionary values.
    :type valuestring:     :py:str

    :return:               GraphAxis object
    :rtype:                :lie_graph:GraphAxis
    """

    # Try parsing the string using default Python json parser
    json_file = open_anything(json_file)
    try:
        json_file = json.load(json_file)
    except IOError:
        logging.error('Unable to decode JSON string')
        return

    return read_dict(json_file, graph=graph, node_key_tag=node_key_tag, edge_key_tag=edge_key_tag,
                     valuestring=valuestring)


def write_json(graph, keystring=None, valuestring=None, default=None, root_nid=None, include_root=False):
    """
    Export a graph to a (nested) JSON structure

    Convert graph representation of the dictionary tree into JSON
    using a nested or flattened representation of the dictionary hierarchy.

    Dictionary keys and values are obtained from the node attributes using
    `keystring` and `valuestring`.  The keystring is set to graph node_key_tag
    by default.

    :param graph:        Graph object to export
    :type graph:         :lie_graph:GraphAxis
    :param keystring:    key used to identify dictionary 'key' in node
                         attributes
    :type keystring:     :py:str
    :param valuestring:  key used to identify dictionary 'value' in node
                         attributes
    :type valuestring:   :py:str
    :param default:      value to use when node value was not found using
                         valuestring.
    :type default:       mixed
    :param include_root: Include the root node in the hierarchy
    :type include_root:  :py:bool
    :param root_nid:     Root node ID in graph hierarchy

    :rtype:              :py:json
    """

    return json.dumps(write_dict(graph, keystring=keystring, valuestring=valuestring, default=default,
                                 root_nid=root_nid, include_root=include_root))