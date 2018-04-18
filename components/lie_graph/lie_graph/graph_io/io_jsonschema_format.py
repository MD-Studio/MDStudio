# -*- coding: utf-8 -*-

"""
file: io_jsonschema_format.py

Functions for building and validating graphs based on a JSON schema definition.
http://json-schema.org
"""

import os
import json
import sys
import logging
import uritools

from lie_graph.graph_axis.graph_axis_class import GraphAxis
from lie_graph.graph_math_operations import graph_join
from lie_graph.graph_io.io_helpers import open_anything
from lie_graph.graph_io.io_jsonschema_format_drafts import JSONSchemaValidatorDraft07, JSONSchemaORMDraft07

if sys.version_info[0] < 3:
    import urlparse
else:
    from urllib import parse as urlparse


def resolve_json_ref(graph):
    """
    Resolve JSON Schema $ref pointers

    :param graph:   Graph to resolve $ref for
    """

    # Get path to current document for resolving relative document $ref
    path = graph.get_root().document_path

    for nid, ref in [(k, v['$ref']) for k, v in graph.nodes.items() if '$ref' in v]:

        # Parse JSON $ref
        parsed = uritools.urisplit(ref)

        # Internal ref to definition
        def_graph = None
        if parsed.fragment and parsed.fragment.startswith('/definitions') and not len(parsed.path):
            result = graph.xpath(parsed.fragment.replace('/definitions', '/'))
            if not result.empty():
                def_graph = result.descendants(include_self=True).copy()

        # Include ref from another JSON Schema
        elif len(parsed.path) and os.path.isfile(os.path.abspath(os.path.join(os.path.dirname(path), parsed.path))):
            external = read_json_schema(os.path.abspath(os.path.join(os.path.dirname(path), parsed.path)))
            fragment = parsed.fragment or 'root'
            result = external.xpath('{0}'.format(fragment.replace('/definitions', '/')))
            if not result.empty():
                def_graph = result.descendants(include_self=True).copy()

        # Merge definitions with target
        if def_graph:
            def_root = def_graph.get_root()
            def_target = graph.getnodes(nid)
            for k, v in def_root.nodes[def_root.nid].items():
                if not k in def_target:
                    def_target.set(k, v)

            if len(def_graph) > 1:
                links = [(nid, child) for child in def_root.children(return_nids=True)]
                def_graph.remove_node(def_root.nid)
                graph_join(graph, def_graph, links=links)

    # Remove 'definitions' from graph
    for nodes in graph.query_nodes(schema_label='definitions'):
        graph.remove_nodes(nodes.descendants(include_self=True, return_nids=True))


def parse_schema_meta_data(metadata):

    if 'draft' not in metadata:
        metadata['draft'] = 'general'
        if '$schema' in metadata:
            url = urlparse.urlparse(metadata['$schema'])
            for path_element in url.path.split('/'):
                if 'draft-' in path_element:
                    metadata['draft'] = path_element.replace('draft-', '')
                    break


def read_json_schema(schema, graph=None, node_key_tag=None, edge_key_tag=None, exclude_args=[],
                     resolve_ref=True):
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
    :param resolve_ref:       Parse JSON schema 'definitions'
    :type resolve_ref:        :py:bool

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

    # What data-blocks to parse, properties by default, definitions if required
    datablock = ['properties']
    if resolve_ref:
        datablock.append('definitions')

    def walk_schema(schema_block, parent=None):

        # Get all JSON schema definitions for this data instance
        attributes = dict([(k, v) for k, v in schema_block.items() if not isinstance(v, dict)
                           and k not in exclude_args])
        node = graph.getnodes(parent)
        node.update(attributes)

        # Store default data or None
        if attributes.get('default') is not None:
            node.set(graph.node_value_tag, attributes.get('default'))

        # For all child elements in datablock, make new node
        # and parse using recursive calls to parse_schema
        for block in schema_block.keys():
            if block in datablock:
                for child, attr in schema_block[block].items():
                    nid = graph.add_node(child)

                    # Register block_name in child attributes
                    attr['schema_label'] = block

                    graph.add_edge(parent, nid)
                    walk_schema(attr, parent=nid)

    walk_schema(json_schema, graph.root)

    # Parse schema meta data
    root = graph.get_root()
    root.set('document_path', os.path.abspath(schema))
    parse_schema_meta_data(root)

    # Resolve JSON Schema $ref
    if resolve_ref:
        resolve_json_ref(graph)

    return graph
