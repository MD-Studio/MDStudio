# -*- coding: utf-8 -*-

"""
file: task_python_type.py

Task for running a Python function in threaded or blocking mode
"""

import logging

from importlib import import_module
from twisted.internet import (reactor, threads)

from lie_graph.graph_mixin import NodeTools
from lie_graph.graph_math_operations import graph_join
from lie_workflow.workflow_task_types.task_base_type import TaskBase, load_task_schema

# Preload Task definitions from JSON schema in the package schema/endpoints/
TASK_SCHEMA = 'workflow_python_task.v1.json'
TASK = load_task_schema(TASK_SCHEMA)


class LoadCustomFunc(NodeTools):

    def load(self):
        """
        Python function or class loader

        Custom Python function can be run on the local machine using a blocking
        or non-blocking task runner.
        These functions are loaded dynamically ar runtime using the Python URI
        of the function as stored in the task 'custom_func' attribute.
        A function URI is defined as a dot-separated string in which the last
        name defines the function name and all names in front the absolute or
        relative path to the module containing the function. The module needs
        to be in the python path.

        Example: 'path.to.module.function'

        :param python_uri: Python absolute or relative function URI
        :type python_uri:  :py:str

        :return:           function object
        """

        func = None
        python_uri = self.get()
        if python_uri:
            module_name = '.'.join(python_uri.split('.')[:-1])
            function_name = python_uri.split('.')[-1]

            try:
                imodule = import_module(module_name)
                func = getattr(imodule, function_name)
                logging.debug(
                    'Load task runner function: {0} from module: {1}'.format(function_name, module_name))
            except (ValueError, ImportError):
                msg = 'Unable to load task runner function: "{0}" from module: "{1}"'
                logging.error(msg.format(function_name, module_name))
        else:
            logging.error('No Python path to function or class defined')

        return func


class PythonTask(TaskBase):
    """
    Task class for running Python functions or classes in threaded
    mode using Twisted `deferToThread`.
    """

    def new(self, **kwargs):
        """
        Implements 'new' abstract base class method to create new
        task node tree.

        Load task from JSON Schema workflow_python_task.v1.json in package
        /schemas/endpoints folder.
        """

        # Do not initiate twice in case method gets called more then once.
        if not len(self.children()):

            logging.info('Init task {0} ({1}) from schema: {2}'.format(self.nid, self.key, TASK_SCHEMA))

            graph_join(self._full_graph, TASK.descendants(),
                       links=[(self.nid, i) for i in TASK.children(return_nids=True)])

            # Set unique task uuid
            self.task_metadata.task_id.set('value', self.task_metadata.task_id.create())

    def run_task(self, callback, errorback, **kwargs):
        """
        Implements run_task method

        Runs Python function or class in threaded mode using Twisted
        'deferToThread' method.

        :param callback:    WorkflowRunner callback method called from Twisted
                            deferToThread when task is done.
        :param errorback:   WorkflowRunner errorback method called from Twisted
                            deferToThread when task failed.
        """

        # Load python function or fail
        python_func = self.custom_func.load()
        if python_func is None:
            errorback(None, self.nid)

        d = threads.deferToThread(python_func, **self.get_input())
        if errorback:
            d.addErrback(errorback, self.nid)
        if callback:
            d.addCallback(callback, self.nid)

        if not reactor.running:
            reactor.run(installSignalHandlers=0)

    def cancel(self):

        self.status = 'aborted'


class BlockingPythonTask(TaskBase):
    """
    Task class for running Python functions or classes in blocking
    mode resulting in the main workflow thread to be blocked until
    a result is returned or an exception is raised.
    """

    def new(self, **kwargs):
        """
        Implements 'new' abstract base class method to create new
        task node tree.

        Load task from JSON Schema workflow_python_task.v1.json in package
        /schemas/endpoints folder.
        """

        # Do not initiate twice in case method gets called more then once.
        if not len(self.children()):

            logging.info('Init task {0} ({1}) from schema: {2}'.format(self.nid, self.key, TASK_SCHEMA))

            graph_join(self._full_graph, TASK.descendants(),
                       links=[(self.nid, i) for i in TASK.children(return_nids=True)])

            # Set unique task uuid
            self.task_metadata.task_id.set('value', self.task_metadata.task_id.create())

    def run_task(self, callback, errorback, **kwargs):
        """
        Implements run_task method

        Runs Python function or class in blocking mode

        :param callback:    WorkflowRunner callback method called when task
                            is done.
        :param errorback:   WorkflowRunner errorback method called when task
                            failed.
        """

        # Load python function or fail
        python_func = self.custom_func.load()
        if python_func is None:
            return errorback('No Python path to function or class defined', self.nid)

        output = None
        try:
            output = python_func(**self.get_input())
        except Exception as e:
            if errorback:
                return errorback(e, self.nid)

        callback(output, self.nid)

    def cancel(self):

        self.status = 'aborted'
