# -*- coding: utf-8 -*-

"""
file: workflow_spec.py

Classes required to build microservice oriented workflow specifications that can
be run using the `Workflow` runner class
"""

import os
import json
import logging
import time
import jsonschema

from lie_system import WAMPTaskMetaData
from lie_graph import GraphAxis
from lie_graph.io.io_json_format import read_dict, write_json
from lie_graph.io.io_helpers import _open_anything

from .common import WorkflowError, _schema_to_data
from .workflow_task_specs import WORKFLOW_ORM

# Path to default workflow JSON schema part of the module
WORKFLOW_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'workflow_schema.json')


class WorkflowSpec(object):
    """
    Interface class for building workflow specifications.
    
    A workflow is a Directed Acyclic Graph (DAG) in wich the nodes represent
    tasks and the edges the connections between them. The Workflow class 
    acts as manager collecting output from tasks and forwarding it to other 
    tasks along the edges.
    The `lie_workflow` DAG follows the workflow principles as described by the
    Workflow Patterns initiative supporting many but not all of the described 
    patterns (http://www.workflowpatterns.com).
    
    The task node is the basic functional unit in the DAG. It accepts input,
    offloads it to a microservice or dedicated Python function or class
    that performs work and collects the returned output. 
    Offloading of work is performed by a dedicated task runner class that 
    knows how to call external microservice or local Python function/class in
    asynchronous or blocking mode.
    In addition to a task node there are nodes required to construct specific
    workflow patterns such as:
    
    * Collect: a node that collects and combines the output of various tasks
      before forwarding it to the next.
    * Choice: a node that makes a choice on the next step to take based on the
      output of another node.
    
    :param init_default: upon class initiation, create default empty workflow.
    :type init_default:  :py:bool
    """
    
    def __init__(self, init_default=True):
        
        self.workflow = None
        
        # Init default empty workflow based on a workflow JSON schema
        if init_default:
            self.new()
    
    def _task_name_to_nid(self, task_name):
        """
        Translate node task name to nid
        """
        
        datatag = self.workflow.node_data_tag
        for nid, node in self.workflow.nodes.items():
            if node.get(datatag) == task_name:
                return nid
    
    def _parse_schema(self, schema):
        """
        Parse a workflow JSON schema from various input sources
        
        Supports already parsed schemas as Python dictionaries and all formats
        supported by the `_open_anything` function that includes: strings,
        files, file objects and URL sources.
        
        :param schema: JSON workflow schema to parse
        :type schema:  mixed
        
        :return:       parsed schema
        :rtype:        :py:dict
        """
        
        # Schema already parsed as dictionary
        if type(schema) == dict:
            return schema
        
        # Try parsing using _open_anything
        schema_file_object = _open_anything(schema)
        if schema_file_object:
            return json.load(schema_file_object)
        else:
            logging.error('Unsupported workflow JSON schema format {0}'.format(schema))
    
    def new(self, schema=WORKFLOW_SCHEMA_PATH):
        """
        Build new (empty) workflow specification based on a JSON schema.
        
        :para schema: JSON schema
        :type schema: format supported by the `_parse_schema` method
        
        TODO: _schema_to_data function is a hack, should be replaced by a solid module
        """
        
        # Parse the schema, no validation performed
        schema_dict = self._parse_schema(schema)
        
        # Build workflow template from schema
        workflow_template = _schema_to_data(schema_dict)
        
        # Validate template
        jsonschema.validate(workflow_template, schema_dict)
        
        # (empty) nodes and edges are usually not available
        for d in ('nodes','edges'):
            if not d in workflow_template:
                workflow_template[d] = {}
        
        # Construct a lie_graph GraphAxis object
        self.workflow = read_dict(workflow_template)
        self.workflow.orm = WORKFLOW_ORM
        
        # Add start node, add WAMP metadata and make root
        nid = self.add_task('start', task_type='Start')
        task_meta = WAMPTaskMetaData()
        
        self.workflow.root = nid
        self.workflow.nodes[self.workflow.root].update(task_meta.dict())
        self.workflow.init_time = int(time.time())
        
        logging.info('Init default empty workflow')
    
    def load(self, workflow, schema=WORKFLOW_SCHEMA_PATH):
        """
        Load workflow specification
        
        Initiate a workflow from a workflow specification or instance thereof.
        Checks if the workflow defines a root node and if that node is a Start
        task.
        
        :param workflow: Predefined workflow object
        :type workflow:  GraphAxis
        """
        
        # Parse the workflow and the schema to validate the workflow
        workflow = self._parse_schema(workflow)
        schema_dict = self._parse_schema(schema)
        
        # Validate workflow specification
        jsonschema.validate(workflow, schema_dict)
        
        # Construct a lie_graph GraphAxis object
        self.workflow = read_dict(workflow)
        self.workflow.orm = WORKFLOW_ORM
        
        if self.workflow.root is None:
            raise WorkflowError('Workflow does not have a root node defined')
        
        if self.workflow.nodes[self.workflow.root]['task_type'] != 'Start':
            raise WorkflowError('Workflow root node is not of type: Start')
        
        logging.info('Load workflow specification. Title: {0}'.format(getattr(self.workflow, 'title', '')))
        logging.info('Description: {0}'.format(getattr(self.workflow, 'description', '')))
    
    def save(self, path=None):
        """
        serialize the workflow specification to JSON
        
        :param path: optionally write JSON string to file
        :type path:  :py:str
        
        :return: serialized workflow
        :rtype:  JSON string
        """
        
        json_string = write_json(self.workflow)
        
        if path:
            assert os.path.exists(os.path.dirname(path)), 'Directory does not exist: {0}'.format(os.path.dirname(path))
            try:
                with open(path, 'w') as json_to_file:
                    json_to_file.write(json_string)
                logging.info('Save workflow {0} to file: {1}'.format(getattr(self.workflow, 'title', ''), path))
            except:
                logging.error('Unable to write workflow to file: {0}'.format(path))
        
        return json_string
    
    def add_task(self, name, task_type='Task', **kwargs):
        """
        Add a new task to the workflow from the set of supported workflow
        task types defined in the workflow ORM.
        
        After a task of a specific type is added to the graph its init_task
        method is called wich adds default and type specific metadata to
        the node attributes. Additional keyword arguments to the `add_task`
        method are passed to the init_task method.
        
        :param name:      Administrative name of the task
        :type name:       :py:str
        :param task_type: Task type to add
        :type task_type:  :py:str
        :param kwargs:    additonal keyword arguments passed to the task
                          init_task method.
        :type kwargs:     :py:dict
        
        :return:          Task node ID (nid) in the graph
        :rtype:           :py:int
        """
        
        # Task type needs to be supported by ORM
        assert type(task_type) == str, 'Workflow task type needs to be of type string'
        assert task_type in self.workflow.orm.mapped_node_types.get('task_type',[]), 'Workflow task type "{0}" not supported'.format(task_type)
        
        # Add the task as node
        nid = self.workflow.add_node(name, task_type=task_type)
        
        # If the task has a `init_task` method, run it.
        # Pass additonal keyword arguments.
        node = self.workflow.getnodes(nid)
        if hasattr(node, 'init_task'):
            node.init_task(**kwargs)
        
        return nid
    
    def connect_task(self, task1, task2):
        """
        Connect tasks by name
        
        :param task1: first task of two tasks to connect
        :type task1:  :py:str
        :param task2: second task of two tasks to connect
        :type task3:  :py:str
        """
        
        nid1, nid2 = None, None
        for node in self.workflow.nodes.values():
            if node['task_name'] == task1:
                nid1 = node['_id']
            elif node['task_name'] == task2:
                nid2 = node['_id']
        
        assert nid1, 'Task {0} not in workflow'.format(task1)
        assert nid2, 'Task {0} not in workflow'.format(task2)
        
        self.workflow.add_edge(nid1, nid2)
    
    def get_task(self, task_name=None, nid=None):
        """
        Return a task by task name or task nid
        
        :param task_name: name of task to return
        :type task_name:  :py:str
        :param nid:       nid of task to return
        :type nid:        :py:int
        """
        
        if task_name:
            nid = self._task_name_to_nid(task_name)
        
        if not nid or not nid in self.workflow.nodes:
            logging.warn('No workflow task with name: {0} or nid: {1}'.format(task_name, nid))
            return None
        
        return self.workflow.getnodes(nid)