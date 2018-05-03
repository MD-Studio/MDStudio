# -*- coding: utf-8 -*-

"""
file: task_base_type.py

Abstract base class defining the Task interface including methods that every
task type should implement
"""

import abc
import pkg_resources
import logging
import json
import os

from lie_graph.graph_mixin import NodeTools
from lie_graph.graph_io.io_jsonschema_format import read_json_schema

from lie_workflow.workflow_common import WorkflowError


def load_task_schema(schema_name):

    task_schema = pkg_resources.resource_filename('lie_workflow', '/schemas/endpoints/{0}'.format(schema_name))
    task_template = read_json_schema(task_schema, exclude_args=['title', 'description', 'schema_label'])
    task_node = task_template.query_nodes(key='task')

    if task_node.empty():
        raise ImportError('Unable to load {0} task defintions'.format(schema_name))
    return task_node


class TaskBase(NodeTools):
    """
    Abstract Base class for workflow Task classes
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def cancel(self):
        """
        Cancel the task
        """

        return

    @property
    def is_active(self):
        """
        Is the task currently active or not
        """

        return self.status in ("submitted","running")

    @property
    def has_input(self):
        """
        Check if input is available

        TODO: does not yet distinguish between predefined input and output
        of other tasks
        """

        return self.task_metadata.input_data.get() is not None

    @property
    def status(self):

        return self.task_metadata.status.get()

    @status.setter
    def status(self, state):

        self.task_metadata.status.value = state

    def next_task(self, exclude_disabled=True):
        """
        Get downstream tasks connected to the current task

        :param exclude_disabled: exclude disabled tasks
        :type exclude_disabled:  :py:bool

        :return:                 downstream task relative to root
        :rtype:                  :py:list
        """

        tasks = []
        for nid in self.neighbors(return_nids=True):
            edge = self.edges.get((self.nid, nid))
            if edge.get('label') == 'task_link':
                task = self.getnodes(nid)
                if exclude_disabled and task.status == 'disabled':
                    continue
                tasks.append(task)

        return tasks

    def previous_task(self):
        """
        Get upstream tasks connected to the current task

        :return: upstream task relative to root
        :rtype:  :py:list
        """

        task_nid = []
        for nid in self.all_parents(return_nids=True):
            edge = self.edges.get((nid, self.nid))
            if edge.get('label') == 'task_link':
                task_nid.append(nid)

        return [self.getnodes(nid) for nid in task_nid]

    def get_input(self):
        """
        Prepare the input data
        """

        input_data = self.task_metadata.input_data.get(default={})
        input_dict = {}
        for key, value in input_data.items():

            # Resolve reference
            if isinstance(value, str):
                input_dict[key] = self._process_reference(value)
            elif isinstance(value, list):
                input_dict[key] = [self._process_reference(v) if isinstance(v, str) else v for v in value]
            else:
                input_dict[key] = value

        return input_dict

    def set_input(self, **kwargs):
        """
        Register task input
        :return:
        """

        data = self.task_metadata.input_data.get(default={})
        data.update(kwargs)
        self.task_metadata.input_data.set('value', data)

    def get_output(self):
        """
        Get task output

        Return dictionary of output data registered in task_metadata.output_data
        If the data is serialized to a local JSON file, load.

        :return:    Output data
        :rtype:     :py:dict
        """

        output = self.task_metadata.output_data.get(default={})
        if '$ref' in output:
            if os.path.exists(output['$ref']):
                output = json.load(open(output['$ref']))
            else:
                raise WorkflowError('Task {0} ({1}), output.json does not exist at: {2}'.format(self.nid, self.key, output['$ref']))

        return output

    def set_output(self, output):
        """
        Set the output of the task.

        If the task is configured to store output to disk (store_output == True)
        the dictionary with output data is serialized to JSON and stored in the
        task directory. A JSON schema $ref directive is added to the project file
        to enable reloading of the output data.
        """

        # Output should be a dictionary for now
        if not isinstance(output, dict):
            raise WorkflowError('Task {0} ({1}). Output should be a dictionary, got {2}'.format(self.nid, self.key, type(output)))

        # Store to file or not
        if self.task_metadata.store_output():
            task_dir = self.task_metadata.workdir.get()
            if task_dir and os.path.exists(task_dir):
                output_json = os.path.join(task_dir, 'output.json')
                json.dump(output, open(output_json, 'w'))
                output = {'$ref': output_json}
            else:
                raise WorkflowError('Task directory does not exist: {0}'.format(task_dir))

        outnode = self.task_metadata.output_data
        if outnode.get() is None:
            outnode.set('value', output)

    def _process_reference(self, ref):
        """
        Resolve reference
        """

        if ref.startswith('$'):
            split = ref.strip('$').split('.')
            ref_nid = int(split[0])
            ref_key = split[1]

            reftask = self.getnodes(ref_nid)
            data = reftask.get_output()

            return data.get(ref_key, None)
        return ref

    def validate(self, key=None):
        """
        Validate task data
        """

        is_valid = True
        for node in self.descendants().query_nodes(required=True):
            if node.get() is None:
                logging.error('Parameter "{0}" is required'.format(node.key))
                is_valid = False

        return is_valid
