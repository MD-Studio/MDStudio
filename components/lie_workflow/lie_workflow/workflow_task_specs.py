# -*- coding: utf-8 -*-

"""
file: task_specs.py

Graph node task classes
"""

import random
import logging
import jsonschema
import json
import time
import os
import copy

from twisted.internet import reactor, defer, threads
from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

from lie_graph.graph_orm import GraphORM
from lie_system import WAMPTaskMetaData

from .common import _schema_to_data

# Get the task schema definitions from the default task_schema.json file
TASK_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'task_schema.json')
task_schema = json.load(open(TASK_SCHEMA_PATH))

logging = Logger()


class _TaskBase(object):
    
    @property
    def status(self):
        
        return self.nodes[self.nid].get('status')
    
    @status.setter
    def status(self, status):
        
        status = status.lower()
        if status in ("ready","submitted","running","failed","aborted","completed","deactivated"):
            self.nodes[self.nid]['status'] = status
        else:
            logging.error('Task status tag {0} not supported'.format(status))
    
    def init_task(self, **kwargs):
        """
        Initiate the task.
        
        Called when adding a new task to the workflow. 
        Initiates an instance of the default task data dictionary and adds
        type specific data to it.
        """
        
        logging.info('Init task {0} ({1}). Update attributes'.format(self.nid, self.task_name))
        
        task_data = _schema_to_data(task_schema, data=kwargs)
        jsonschema.validate(task_data, task_schema)
        
        self.nodes[self.nid].update(task_data)
    
    def update_session(self, session_data=None):
        """
        Update a (WAMP) session
        """
        
        current_session = self.nodes[self.nid].get('session', {})
        updated_session = WAMPTaskMetaData(metadata=current_session)
        
        if session_data:
            updated_session.update(session_data)
        
        self.nodes[self.nid]['session'] = updated_session.dict()
        return self.nodes[self.nid]['session']
    
    def get_input(self):
        """
        Prepaire the input data
        """
        
        input_dict = {}
        for key,value in self.nodes[self.nid].get('input_data', {}).items():
            
            # Resolve reference
            if type(value) == str and value.startswith('$'):
                split = value.strip('$').split('.')
                ref_nid = int(split[0])
                ref_key = split[1]
                
                input_dict[key] = self._full_graph.nodes[ref_nid]['output_data'].get(ref_key, None)
            else:
                input_dict[key] = value
        
        return input_dict
        
    def cancel(self):
        """
        Cancel the task
        """
        
        if not self.active:
            logging.info('Unable to cancel task {0} ({1}) not active'.format(self.nid, self.task_name))
            return
        
        self.status = 'aborted'
        self.active = False
        logging.info('Canceled task {0} ({1})'.format(self.nid, self.task_name))


class Task(_TaskBase):
    """
    A task runner class that runs Python functions or classes in
    threaded mode using Twisted `deferToThread`. 
    """
    
    def run_task(self, runner, callback=None, errorback=None):
        
        logging.info('running "{0}"'.format(self.task_name))
        
        # Get task session
        session = WAMPTaskMetaData(metadata=self.nodes[self.nid].get('session', {}))
        
        d = threads.deferToThread(runner,
                                  session=session.dict(), 
                                  **self.get_input())
        if errorback:
            d.addErrback(errorback, self.nid)
        if callback:
            d.addCallback(callback, self.nid)
        
        if not reactor.running:
            reactor.run(installSignalHandlers=0)

class WampTask(_TaskBase):
    
    #@inlineCallbacks
    def run_task(self, runner, callback, errorback=None):
        
        method_url = unicode(self.uri)
        logging.info('Task {0} ({1}) running on {2}'.format(self.nid, self.task_name, method_url))
        
        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=self.nodes[self.nid].get('session',{}))
        
        # Call the service
        deferred = runner(method_url, session=session.dict(), **self.get_input())

        # Attach error callback
        if errorback:
            deferred.addErrback(errorback, self.nid)

        # Attach callback if needed
        deferred.addCallback(callback, self.nid)
        

class BlockingTask(_TaskBase):
    """
    A task runner class that runs Python functions or classes in
    blocking mode resulting in the main workflow thread to be 
    blocked until a result is returned or an exception is raised.
    """
    
    def run_task(self, runner, callback, errorback=None):
        
        logging.info('running "{0}"'.format(self.task_name))
        
        # Get task session
        session = WAMPTaskMetaData(metadata=self.nodes[self.nid].get('session', {}))
        
        try:
            output = runner(session=session.dict(), 
                            **self.get_input())
        except Exception as e:
            if errorback:
                return errorback(e, self.nid)
            else:
                logging.error('Error in running task {0} ({1})'.format(self.nid, self.task_name))
                logging.error(e)
                return
        
        callback(output, self.nid)

class StartTask(_TaskBase):
    """
    Workflow start task
    
    Responsible for handling intitial workflow input and pre-processing
    """
        
    def run_task(self, runner, callback, errorback=None):
        
        session = WAMPTaskMetaData(metadata=self.nodes[self.nid].get('session', {}))
        
        # Check input
        status = 'completed'
        self.nodes[self.nid]['output_data'] = self.get_input()
        if 'file' in self.nodes[self.nid]['output_data']:
            path = self.nodes[self.nid]['output_data']['file']
            if not os.path.exists(path):
                logging.error('File does not exist: {0}'.format(path))
                status = 'failed'
            else:
                with open(path) as inp:
                    self.nodes[self.nid]['output_data']['file'] = inp.read()
        
        session.status = status
        session._metadata['utime'] = int(time.time())
        
        callback({'session': session.dict()}, self.nid)


class Choice(_TaskBase):
    
    def run_task(self, runner, callback=None, errorback=None):
        
        connections = self.children(return_nids=True)
        gofor = random.choice(connections)
        
        print("make a choice between: {0}, go for {1}".format(connections, gofor))
        for task in [t for t in connections if t != gofor]:
            self._full_graph.nodes[task]['status'] = 'disabled'
        
        self.nodes[self.nid]['output_data'] = self.nodes[self.nid].pop('input')
        self.status = 'failed'


class Collect(_TaskBase):
    """
    Reducer class
    
    Waits for all parent tasks to finish and collects the output
    """
    
    def run_task(self, runner, callback, errorback=None):
        
        session = WAMPTaskMetaData(metadata=self.nodes[self.nid].get('session', {}))
        
        # Get all nodes connected to self. In the directed workflow graph these
        # are the ancestors
        ancestors = [nid for nid,adj in self.adjacency.items() if self.nid in adj]
        
        # Check if there are failed tasks among the ancestors and if we are
        # allowed to continue with less
        failed_ancestors = [tid for tid in ancestors if self._full_graph.nodes[tid]['status'] in ('failed','aborted')]
        if failed_ancestors:
            logging.error('Failed parent tasks detected. Unable to collect all output')
            session.status = 'failed'
            session._metadata['utime'] = int(time.time())
            callback({'session': session.dict()}, self.nid)
        
        # Check if the ancestors are al completed
        if all([self._full_graph.nodes[tid]['status'] in ('completed','disabled') for tid in ancestors]):
            logging.info('Task {0} ({1}): Output of {2} parent tasks available, continue'.format(self.nid, self.task_name, len(ancestors)))
            
            # Collect output of previous tasks and apply data mapper
            collected_output = []
            for tid in ancestors:
                mapper = self._full_graph.edges[(tid, self.nid)].get('data_mapping', {})
                collected_output.append(dict([(mapper.get(k,k),v) for k,v in self._full_graph.nodes[tid]['output_data'].items()]))
            
            session.status = 'completed'
            session._metadata['utime'] = int(time.time())
            
            output = {'session': session.dict()}
            output.update(runner(collected_output))
            callback(output, self.nid)
            
        else:
            # Output collection not complete. Reset task status to ready and evaluate again at next pass
            logging.info('Task {0} ({1}): Not all output available yet'.format(self.nid, self.task_name))
            self.active = False
            self.status = 'ready'
            callback({'session': session.dict()}, self.nid)


WORKFLOW_ORM = GraphORM(inherit=False)
WORKFLOW_ORM.map_node(StartTask, {'task_type':'Start'})
WORKFLOW_ORM.map_node(Task, {'task_type':'Task'})
WORKFLOW_ORM.map_node(Choice, {'task_type':'Choice'})
WORKFLOW_ORM.map_node(Collect, {'task_type':'Collect'})
WORKFLOW_ORM.map_node(BlockingTask, {'task_type': 'BlockingTask'})
WORKFLOW_ORM.map_node(WampTask, {'task_type': 'WampTask'})