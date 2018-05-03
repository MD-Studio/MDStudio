# -*- coding: utf-8 -*-

"""
file: workflow_spec.py

Classes required to build microservice oriented workflow specifications
that can be run using the `Workflow` runner class
"""

import os
import logging
import pkg_resources

from lie_graph import GraphAxis
from lie_graph.graph_io.io_jgf_format import write_jgf, read_jgf
from lie_graph.graph_io.io_jsonschema_format import read_json_schema
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools
from lie_graph.graph_helpers import renumber_id

from lie_workflow import __version__
from lie_workflow.workflow_common import WorkflowError
from lie_workflow.workflow_task_types import WORKFLOW_ORM

# Path to default workflow JSON schema part of the module
workflow_metadata_template = pkg_resources.resource_filename('lie_workflow',
                                                             '/schemas/resources/workflow_metadata_template.json')


class WorkflowSpec(object):
    """
    Interface class for building workflow specifications.

    A workflow is a Directed Acyclic Graph (DAG) in which the nodes represent
    tasks and the edges the connections between them. The Workflow class
    acts as manager collecting output from tasks and forwarding it to other
    tasks along the edges (push execution).
    The `lie_workflow` DAG follows the workflow principles as described by the
    Workflow Patterns initiative supporting many but not all of the described
    patterns (http://www.workflowpatterns.com).

    The task node is the basic functional unit in the DAG. It accepts task
    configuration and input from other task nodes and provides these to the
    specific task that may be a microservice or dedicated Python function or
    class that performs work and collects the returned output.
    Offloading of work is performed by a dedicated task runner class that
    knows how to call external microservice or local Python function/class in
    asynchronous or blocking mode.
    In addition to a task node there are nodes required to construct specific
    workflow patterns such as:

    * Collect: a node that collects and combines the output of various tasks
      before forwarding it to the next.
    * Choice: a node that makes a choice on the next step to take based on the
      output of another node.

    """

    def __init__(self, workflow=None, **kwargs):
        """
        Init the workflow specification

        If no workflow provided init a default empty one.
        Additional keyword parameters are used to update the workflow project
        metadata.

        :param workflow: workflow specification
        :type workflow:  :lie_graph:GraphAxis
        :param kwargs:   additional keyword arguments used to update project
                         metadata
        :type kwargs:    :py:dict
        """

        self.workflow = workflow

        if self.workflow is None:
            self.new()
        elif not isinstance(workflow, GraphAxis):
            raise WorkflowError('Not a valid workflow {0}'.format(workflow))

        # Update project metadata
        if kwargs:
            project_metadata = self.workflow.query_nodes(key='project_metadata')
            project_metadata.descendants().update(kwargs)

    def __len__(self):
        """
        Implement class __len__

        :return: return number of tasks in workflow
        """

        return len(self.workflow.query_nodes(format='task'))

    def add_task(self, task_name, task_type='PythonTask', **kwargs):
        """
        Add a new task to the workflow from the set of supported workflow
        task types defined in the workflow ORM.

        The 'new' method of each task type is called at first creation to
        construct the task data object in the graph.
        Additional keyword arguments provided to the 'add_task' method will
        used to update the task data

        :param task_name: Administrative name of the task
        :type task_name:  :py:str
        :param task_type: Task type to add
        :type task_type:  :py:str
        :param kwargs:    additional keyword arguments passed to the task
                          init_task method.
        :type kwargs:     :py:dict

        :return:          Task object
        """

        # Task type needs to be supported by ORM
        supported_task_types = self.workflow.orm.mapped_node_types.get('task_type', [])
        if task_type not in supported_task_types:
            raise WorkflowError('Workflow task type "{0}" not supported. Needs to be one of {1}'.format(task_type,
                                                                                    ', '.join(supported_task_types)))

        # Add the task as node to the workflow graph. The task 'new' method is
        # called for initial task initiation.
        nid = self.workflow.add_node(task_name, task_type=task_type, format='task')

        # Update Task metadata
        task = self.workflow.getnodes(nid)
        task.descendants().update(kwargs)

        # If this is the first task added, set the root to task nid
        if len(self.workflow.query_nodes(format='task')) == 1:
            self.workflow.root = nid

        return task

    def connect_task(self, task1, task2, *args, **kwargs):
        """
        Connect tasks by task ID (graph nid)

        Creates the directed graph edge connecting two tasks (nodes) together.
        An edge also defines which parameters in the output of one task serve
        as input for another task and how they are named.

        Parameter selection is defined by all additional arguments and keyword
        arguments provided to `connect_task`. Keyword arguments also define the
        name translation of the argument.

        :param task1:         first task of two tasks to connect
        :type task1:          :py:int
        :param task2:         second task of two tasks to connect
        :type task2:          :py:int
        """

        assert task1 in self.workflow.nodes, 'Task {0} not in workflow'.format(task1)
        assert task2 in self.workflow.nodes, 'Task {0} not in workflow'.format(task2)

        eid = self.workflow.add_edge(task1, task2, label='task_link', data_mapping=kwargs, data_select=list(args))

        return eid

    def get_tasks(self, tid=None):
        """
        Return a task by task ID (graph nid)

        :param tid:       nid of task to return
        :type tid:        :py:int
        """

        tasks = self.workflow.query_nodes(format="task")
        if len(tasks) == 1:
            return [tasks]

        return list(tasks)

    def new(self, schema=workflow_metadata_template):
        """
        Construct new empty workflow based on template JSON Schema file

        :param schema: JSON schema
        """

        # Build workflow template from schema
        template = read_json_schema(schema, exclude_args=['title', 'description', 'schema_label'])
        self.workflow = template.query_nodes(key='project_metadata').descendants(include_self=True).copy()
        self.workflow.is_directed = True
        self.workflow.node_tools = NodeAxisTools
        self.workflow.orm = WORKFLOW_ORM
        renumber_id(self.workflow, 1)

        # Update workflow meta-data
        metadata = self.workflow.query_nodes(key='project_metadata')
        metadata.create_time.set()
        metadata.user.set()
        metadata.version.set('value', __version__)

        logging.info('Init default empty workflow')

    def load(self, workflow):
        """
        Load workflow specification

        Initiate a workflow from a workflow specification or instance thereof.

        :param workflow: Predefined workflow object
        :type workflow:  GraphAxis
        """

        # Construct a workflow GraphAxis object
        self.workflow = read_jgf(workflow)
        self.workflow.node_tools = NodeAxisTools
        self.workflow.orm = WORKFLOW_ORM

        assert self.workflow.root is not None, WorkflowError('Workflow does not have a root node defined')

        # Get metadata
        metadata = self.workflow.query_nodes(key='project_metadata')
        logging.info('Load workflow "{0}"'.format(metadata.title.get()))
        logging.info('Created: {0}, updated: {1}'.format(metadata.create_time.get(), metadata.update_time.get()))
        logging.info('Description: {0}'.format(metadata.description.get()))

    def save(self, path=None):
        """
        Serialize the workflow specification to a graph JSON format (.jgf)

        :param path: optionally write JSON string to file
        :type path:  :py:str

        :return: serialized workflow
        :rtype:  :py:str
        """

        # Update workflow meta-data
        metadata = self.workflow.query_nodes(key='project_metadata')

        json_string = write_jgf(self.workflow)
        if path:
            pred = os.path.exists(os.path.dirname(path))
            msg = 'Directory does not exist: {0}'.format(os.path.dirname(path))
            assert pred, msg
            try:
                with open(path, 'w') as json_to_file:
                    json_to_file.write(json_string)
                logging.info('Save workflow "{0}" to file: {1}'.format(metadata.title.get(), path))
            except IOError:
                logging.error('Unable to write workflow to file: {0}'.format(path))

        return json_string