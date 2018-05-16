# -*- coding: utf-8 -*-

"""
file: haddock_model.py

Functions to build and manipulate a graph based data model representing a
Haddock project.
"""

import os
import logging
import pkg_resources

from lie_graph import GraphAxis
from lie_graph.graph_math_operations import graph_join, graph_axis_update
from lie_graph.graph_io.io_web_format import read_web, write_web
from lie_graph.graph_io.io_jsonschema_format import read_json_schema
from lie_graph.graph_axis.graph_axis_methods import node_descendants
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools

from haddock_model_classes import haddock_orm
from haddock_helper_methods import new_incremented_param_name, validate_model

schemadir = pkg_resources.resource_filename('lie_haddock', '/schemas/endpoints')


def remove_haddock_data_block(project, block_id, multiple=False):
    """
    Remove a single parameter to full data block from the project based on
    block ID.

    :param project:   Haddock project containing data
    :type project:    :lie_graph:GraphAxis
    :param block_id:  identifier of data block to remove
    :type block_id:   :py:str
    :param multiple:  remove multiple if found
    :type multiple:   :py:bool

    :return:          removal was successful
    :rtype:           :py:bool
    """

    # Get data block from project by block ID
    data_block = None
    for block in block_id.split('.'):
        if data_block is None:
            data_block = project.query_nodes(key=block)
        else:
            data_block = data_block.descendants(include_self=True).query_nodes(key=block)

    # Parameter not found
    if data_block.empty():
        logging.warning('Unable to remove data block "{0}". Not found in project'.format(block_id))
        return False

    # Remove multiple?
    if len(data_block) > 1:
        if not multiple:
            logging.warning('Multiple data blocks type "{0}". Set "multiple" to True to remove all'.format(block_id))
            return False

    logging.info('Remove parameter "{0}", {1} instances'.format(block_id, len(data_block)))
    for nid in data_block.nodes():
        to_delete = node_descendants(project, nid, project.root, include_self=True)
        project.remove_nodes(to_delete)

    return True


def load_project(project_id):
    """
    Load a project from file or database

    This method will always return a GraphAxis based data model that may be empty
    if project loading failed.

    TODO: add universal check if string is file path, else load from database

    :param project_id: project identifier as file path or database entry name
    :type project_id:  :py:str

    :return:           Haddock project data model
    :rtype:            :lie_graph:GraphAxis
    """

    project = GraphAxis()
    project.node_tools = NodeAxisTools

    # Project ID is (absolute) path to file
    if os.path.isfile(project_id):
        project = read_web(project_id, graph=project, auto_parse_format=True)

    project.orm = haddock_orm

    return project


def new_project(project_id):
    """
    Create a new haddock project based on base project template

    :param project_id: project identifier to use for new project
    :type project_id:  :py:str

    :return:           Haddock project data model
    :rtype:            :lie_graph:GraphAxis
    """

    # Create new project block
    template_file = os.path.join(schemadir, '{0}.json'.format('haddock-project-request.v1'))
    new_block = new_haddock_data_block_from_template(template_file)

    # Return a copy of only the HaddockRunParameters
    # This removes the node containing the JSON Schema meta-data
    project = new_block.query_nodes(haddock_type='HaddockRunParameters')
    project = project.descendants(include_self=True).copy()

    return project


def save_project(project, project_id):
    """
    Save a project to a file or database

    :param project:    project data model to save
    :type project:     :lie_graph:GraphAxis
    :param project_id: project identifier as file path or database entry name
    :type project_id:  :py:str
    """

    if os.path.isfile(project_id):
        logging.info("Update project: {0}".format(project_id))

    with open(project_id, 'w') as pf:
        pf.write(write_web(project))


def new_haddock_data_block_from_template(template):
    """
    Create a new Haddock data block based on a JSON schema template

    :param template:    data block template file name
    :type template:     :py:str

    :return:            graph based data model representing the data block
    :rtype:             :lie_graph:GraphAxis
    """

    if not os.path.isfile(template):
        raise IOError('No such JSON schema file: {0}'.format(template))

    # Parse the schema to a GraphAxis object
    graph = GraphAxis()
    graph.node_tools = NodeAxisTools

    schema_dict = read_json_schema(template, graph=graph)
    schema_dict.orm = haddock_orm

    # Check if something was parsed
    if schema_dict.empty():
        logging.error('Error parsing JSON schema file: {0}. Empty data model'.format(template))

    return schema_dict


def new_parameter_block(project, template, haddock_type, max_mult=None, attach=None):
    """
    Create a new Haddock parameter data block and add it to a project

    Creates a new parameter block based on a JSON schema defined by `template`
    as a file path to the schema files in located in the package
    /schema/endpoints directory.
    The data block itself is defined by the haddock_type.

    :param project:      Haddock project to add new parameter block to
    :type project:       :lie_graph:GraphAxis
    :param template:     JSON Schema template file describing parameter block
    :type template:      :py:str
    :param haddock_type: Main Haddock type of the parameter block to add
    :type haddock_type:  :py:str
    :param max_mult:     maximum number of instances of the given parameter
                         block as identified by the Haddock type
    :type max_mult:      :py:int
    :param attach:       node name to attach new block to
    :type attach:        :py:str

    :return:             newly added block ID and Haddock project
    """

    # Add template block to project
    target_attach_node = project
    target_attach_nid = project.root
    if attach:
        xpath = project.xpath(attach, sep='.')
        if xpath.empty():
            logging.error('Target point not found in graph: {0}'.format(attach))
            return
        target_attach_nid = xpath.nid
        target_attach_node = xpath.descendants()

    # Check if we are allowed to create multiple parameter blocks of type
    curr_blocks = target_attach_node.query_nodes(haddock_type=haddock_type)
    if max_mult:
        if len(curr_blocks) >= max_mult:
            logging.error('HADDOCK does not support more than {0} {1} definitions'.format(max_mult, haddock_type))
            return None, project

    # Create new block
    template_file = os.path.join(schemadir, '{0}.json'.format(template))
    new_block = new_haddock_data_block_from_template(template_file)

    # Get the template haddock type and block_id
    new_block = new_block.query_nodes(haddock_type=haddock_type)
    if new_block.empty():
        logging.error('No {0} definition in {1} template'.format(haddock_type, template))
        return None, project

    block_id = new_block.key
    new_block.key = new_incremented_param_name(block_id, curr_blocks.keys())

    mapping = graph_join(project, new_block.descendants(include_self=True), [(target_attach_nid, new_block.nid)])
    logging.info('Add "{0}" template entry to the project'.format(new_block.key))

    # Get path (block_id) to newly added node
    np = project.getnodes(mapping[new_block.nid])

    return np.path(), project


def edit_parameter_block(project, block_id, data):
    """
    Edit existing Haddock project data based on block ID

    Nested 'data' dictionaries will be treated as hierarchical data structures
    and updated as such.

    :param project:   Haddock project containing data
    :type project:    :lie_graph:GraphAxis
    :param block_id:  primary data block identifier
    :type block_id:   :py:str
    :param data:      data key, value pairs to update
    :type data:       :py:dict

    :return:          updated data block
    :rtype:           :lie_graph:GraphAxis
    """

    # Get data block from project by block ID
    data_block = project.xpath(block_id, sep='.').descendants(include_self=True)

    # Log a warning if data block not found
    if data_block.empty():
        logging.warning('Data block with ID "{0}" not in Haddock project'.format(block_id))
        return data_block

    # (Recursive) update data
    graph_axis_update(data_block, data)

    # Validate data
    did_validate_successfully = validate_model(data_block)
    if not did_validate_successfully:
        logging.warning('Validation failed for parameter {0}. Check the log and fix.'.format(block_id))

    return data_block
