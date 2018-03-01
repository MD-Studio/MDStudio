# -*- coding: utf-8 -*-

"""
file: io_web_format.py

Functions for reading and writing hierarchical data structures defined in the
Spider data modelling package as .web format files.

A .web format defines data blocks containing key, value pairs or Array data
as hierarchically nested blocks enclosed using braces '(' and '),' and indented
for visual clarity.

Every data item in the format is written on a new line and is either a single
item usually combined into an array like:

    key = FloatArray (
        1.0,
        2.0,
    )

or a key, value pair as: 'key = value,'.
The type of any piece of data is loosely defined by a type identifier in front
of every new data block that closely reassembles a Python style class name.
The 'FloatArray' identifier in the expression above would be an example.
These identifiers are usually coupled to classes in charge of data exchange
by an object relations mapper such as the one used in the lie_graph package.
"""

import logging
import sys

from lie_graph.graph_axis.graph_axis_class import GraphAxis
from lie_graph.graph_axis.graph_axis_methods import node_parent
from lie_graph.graph_io.io_helpers import open_anything, FormatDetect

if sys.version_info[0] < 3:
    import StringIO
else:
    from io import StringIO


def read_web(web, graph=None, orm_data_tag='type', node_key_tag=None, edge_key_tag=None,
             auto_parse_format=False, array_to_nodes=True):
    """
    Import hierarchical data structures defined in the Spider .web format

    The data block type identifiers used in the .web format are stored in
    the nodes using the `orm_data_tag` attribute. These can be used by the
    Graph ORM mapper for custom data exchange in the graph.

    :param web:               Spider .web data format to import
    :type web:                file, string, stream or URL
    :param graph:             graph object to import TGF data in
    :type graph:              :lie_graph:Graph
    :param orm_data_tag:      data key to use for .web data identifier
    :type orm_data_tag:       :py:str
    :param node_key_tag:      data key to use for parsed node labels.
    :type node_key_tag:       :py:str
    :param edge_key_tag:      data key to use for parsed edge labels.
    :type edge_key_tag:       :py:str
    :param auto_parse_format: automatically detect basic format types
    :type auto_parse_format:  :py:bool
    :param array_to_nodes:    store Array type items as nodes instead of a list
    :type array_to_nodes:     :py:bool

    :return:                  Graph object
    :rtype:                   :lie_graph:Graph
    """

    web_file = open_anything(web)
    if not isinstance(graph, GraphAxis):
        graph = GraphAxis()

    # Define node/edge data labels
    if node_key_tag:
        graph.node_key_tag = node_key_tag
    if edge_key_tag:
        graph.edge_key_tag = edge_key_tag

    # Auto-convert format types
    if auto_parse_format:
        autoformat = FormatDetect()
        logging.info('Init automatic format conversion')

    curr_obj_nid = None
    object_open_tags = 0
    object_close_tags = 0
    array_store = []
    for i, line in enumerate(web_file.readlines()):
        line = line.strip()
        if len(line):

            # Detect start of new object definition
            if line.endswith('('):

                # Process data
                meta_data = [n.strip() for n in line.strip('(').split('=', 1)]
                ddict = {orm_data_tag: meta_data[-1]}
                if len(ddict) > 1:
                    ddict[node_key_tag] = ddict[0]

                # Clear the array store
                array_store = []

                # First object defines graph root
                if graph.empty():
                    curr_obj_nid = graph.add_node(meta_data[0], **ddict)
                    graph.root = curr_obj_nid

                # Add new object as child of current object
                else:
                    child_obj_nid = graph.add_node(meta_data[0], **ddict)
                    graph.add_edge(curr_obj_nid, child_obj_nid)
                    curr_obj_nid = child_obj_nid

                object_open_tags += 1

            # Detect end of object definition
            elif line.startswith(')'):

                # If there is data in the array store, add it to node
                if len(array_store):
                    array_node = graph.getnodes(curr_obj_nid)
                    array_node.set(graph.node_value_tag, array_store)

                # Move one level up the object three
                curr_obj_nid = node_parent(graph, curr_obj_nid, graph.root)
                object_close_tags += 1

            # Parse object parameters
            else:

                # Parse key,value pairs and add as leaf node
                params = [n.strip() for n in line.strip(',').split('=', 1)]
                if auto_parse_format:
                    params = [autoformat.parse(v) for v in params]

                if '=' in line and len(params) == 2:
                    leaf_nid = graph.add_node(params[0])
                    graph.add_edge(curr_obj_nid, leaf_nid)

                    leaf_node = graph.getnodes(leaf_nid)
                    leaf_node.set(graph.node_value_tag, params[1])

                # Parse single values as array data
                elif len(params) == 1:

                    # Store array items as nodes
                    if array_to_nodes:
                        leaf_nid = graph.add_node('array_item')
                        graph.add_edge(curr_obj_nid, leaf_nid)

                        leaf_node = graph.getnodes(leaf_nid)
                        leaf_node.set(graph.node_value_tag, params[0])
                    else:
                        array_store.extend(params)

                else:
                    logging.warning('Unknown .web data formatting on line: {0}, {1}'.format(i, line))

    web_file.close()

    # Object blocks opening '(' and closing ')' tag count should be balanced
    assert object_open_tags == object_close_tags, 'Unbalanced object block, something is wrong with the file format'

    return graph


def write_web(graph, orm_data_tag='type', node_key_tag=None, indent=2):
    """
    Export a graph in Spyder .web format

    .. note::
    Web graph export uses the Graph iternodes and iteredges methods to retrieve
    nodes and edges and 'get' the data labels. The behaviour of this process is
    determined by the single node/edge mixin classes and the ORM mapper.

    :param graph:         Graph object to export
    :type graph:          :lie_graph:Graph
    :param orm_data_tag:  data key to use for .web data identifier
    :type orm_data_tag:   :py:str
    :param node_key_tag:  node data key
    :type node_key_tag:   :py:str
    :param indent:        .web file white space indentation level
    :type indent:         :py:int

    :return:              Spyder .web graph representation
    :rtype:               :py:str
    """

    # Define node data tags to export
    node_key_tag = node_key_tag or graph.node_key_tag
    node_value_tag = graph.node_value_tag

    # Create empty file buffer
    string_buffer = StringIO.StringIO()

    # Traverse node hierarchy
    def _walk_dict(node, indent_level):

        # First, collect all leaf nodes and write
        for leaf in [n for n in node.children() if n.isleaf]:

            # Format 'Array' types when they are list style leaf nodes
            if 'Array' in leaf.get(orm_data_tag, ''):
                string_buffer.write('{0}{1} = {2} (\n'.format(' ' * indent_level,
                                                             leaf.get(node_key_tag),
                                                             leaf.get(orm_data_tag)))

                array_indent = indent_level + indent
                for array_type in leaf.get(node_value_tag, default=[]):
                    string_buffer.write('{0}{1},\n'.format(' ' * array_indent, array_type))

                string_buffer.write('{0}),\n'.format(' ' * indent_level))

            # Format key, value pairs
            else:
                string_buffer.write('{0}{1} = {2},\n'.format(' ' * indent_level,
                                                             leaf.get(node_key_tag),
                                                             leaf.get(node_value_tag, default='')))

        # Second, process child non-leaf nodes
        for child in [n for n in node.children() if not n.isleaf]:

            # Write block header
            string_buffer.write('{0}{1} = {2} (\n'.format(' ' * indent_level,
                                                          child.get(node_key_tag),
                                                          child.get(orm_data_tag)))

            # Indent new data block one level down
            indent_level += indent

            # Format 'Array' types when items are stored as nodes
            if 'Array' in child.get(orm_data_tag, ''):
                for array_type in child.children():
                    string_buffer.write('{0}{1},\n'.format(' ' * indent_level,
                                                           array_type.get(node_value_tag)))
            else:
                _walk_dict(child, indent_level)

            # Close data block and indent one level up
            indent_level -= indent
            string_buffer.write('{0}),\n'.format(' ' * indent_level))

    rootnode = graph.getnodes(graph.root)
    string_buffer.write('{0} (\n'.format(rootnode.get(orm_data_tag)))
    _walk_dict(rootnode, indent)
    string_buffer.write(')\n')

    # Reset buffer cursor
    string_buffer.seek(0)
    return string_buffer.read()