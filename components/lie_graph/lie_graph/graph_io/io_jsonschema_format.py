# -*- coding: utf-8 -*-

"""
file: io_jsonschema_format.py

Functions for building and validating graphs based on a JSON schema definition.
http://json-schema.org
"""

import json
import sys
import logging

from lie_graph.graph_axis.graph_axis_class import GraphAxis
from lie_graph.graph_io.io_helpers import open_anything
from lie_graph.graph_io.io_jsonschema_format_drafts import JSONSchemaValidatorDraft07, JSONSchemaORMDraft07

if sys.version_info[0] < 3:
    import urlparse
else:
    from urllib import parse as urlparse


def parse_schema_meta_data(metadata):

    if 'draft' not in metadata:
        metadata['draft'] = 'general'
        if '$schema' in metadata:
            url = urlparse.urlparse(metadata['$schema'])
            for path_element in url.path.split('/'):
                if 'draft-' in path_element:
                    metadata['draft'] = path_element.replace('draft-', '')
                    break


def read_json_schema(schema, graph=None, node_key_tag=None, edge_key_tag=None, exclude_args=[]):
    """
    Import hierarchical data structures defined in a JSON schema format

    :param schema:            JSON Schema data format to import
    :type schema:             file, string, stream or URL
    :param graph:             graph object to import TGF data in
    :type graph:              :lie_graph:Graph
    :param node_key_tag:      data key to use for parsed node labels.
    :type node_key_tag:       :py:str
    :param edge_key_tag:      data key to use for parsed edge labels.
    :type edge_key_tag:       :py:str
    :param exclude_args:      JSON schema arguments to exclude from import
    :type exclude_args:       :py:list

    :return:                  Graph object
    :rtype:                   :lie_graph:Graph
    """

    # Try parsing the string using default Python json parser
    json_schema = open_anything(schema)
    try:
        json_schema = json.load(json_schema)
    except IOError:
        logging.error('Unable to decode JSON string')
        return

    if not isinstance(graph, GraphAxis):
        graph = GraphAxis()

    if graph.empty():
        rid = graph.add_node('root')
        graph.root = rid

    # Define node/edge data labels
    if node_key_tag:
        graph.node_key_tag = node_key_tag
    if edge_key_tag:
        graph.edge_key_tag = edge_key_tag

    # Build JSON schema parser ORM with format specific conversion classes
    graph.node_tools = JSONSchemaValidatorDraft07
    graph.orm = JSONSchemaORMDraft07

    def walk_schema(schema_block, parent=None):

        # Get all JSON schema definitions for this data instance
        attributes = dict([(k, v) for k, v in schema_block.items() if not isinstance(v, dict)
                           and k not in exclude_args])
        graph.nodes[parent].update(attributes)
        node = graph.getnodes(parent)

        # Store default data or None
        if attributes.get('default') is not None:
            node.set(graph.node_value_tag, attributes.get('default'))

        # For all child elements in properties, make new node
        # and parse using recursive calls to parse_schema
        if 'properties' in schema_block:
            for child, attr in schema_block['properties'].items():
                nid = graph.add_node(child)
                graph.add_edge(parent, nid)
                walk_schema(attr, parent=nid)

    walk_schema(json_schema, graph.root)

    # Parse schema meta data
    parse_schema_meta_data(graph.getnodes(graph.root))

    return graph
