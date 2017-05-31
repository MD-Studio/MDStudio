# -*- coding: utf-8 -*-

import random
import logging
import jsonschema
import time
import os

from   twisted.internet         import reactor, defer, threads
from   twisted.internet.defer   import inlineCallbacks
from   lie_graph.graph_orm      import GraphORM

from   .task_metadata           import task_schema

# Init basic logging
logging.basicConfig(level=logging.DEBUG)

def _schema_to_data(schema, data=None):
    
    default_data = {}
    
    required = schema.get('required', [])
    properties = schema.get('properties',{})
    
    for key,value in properties.items():
        if key in required:
            default_data[key] = value.get('default')
    
    # Update with existing data
    if data:
        default_data.update(data)
    
    return default_data

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
        
        logging.info('Init task {0}. Update attributes'.format(self.nid))
        
        task_data = _schema_to_data(task_schema, data=kwargs)
        jsonschema.validate(task_data, task_schema)
        
        self.nodes[self.nid].update(task_data)

class Task(_TaskBase):
    
    def run_task(self, runner, callback=None, errorback=None):
        
        logging.info('running "{0}"'.format(self.task_name))
        
        d = threads.deferToThread(runner.task, self.nodes[self.nid])
        if errorback:
            d.addErrback(errorback, self.nid)
        if callback:
            d.addCallback(callback)
        
        if not reactor.running:
            reactor.run(installSignalHandlers=0)
            
class StartTask(_TaskBase):
    
    def init_task(self, **kwargs):
        """
        Initiate the task.
        """
        
        logging.info('Init task {0}. Update attributes'.format(self.nid))
        
        task_data = _schema_to_data(task_schema, data=kwargs)
        jsonschema.validate(task_data, task_schema)
        
        # Add Start Task specific metadata
        task_data.update({'project_title': None})
        
        self.nodes[self.nid].update(task_data)
        
    def run_task(self, runner, callback=None, errorback=None):
        
        # Check input
        status = 'completed'
        if 'input' in self.nodes[self.nid]:
            if 'file' in self.nodes[self.nid]['input']:
                if not os.path.exists(self.nodes[self.nid]['input']['file']):
                    logging.error('File does not exist: {0}'.format(self.nodes[self.nid]['input']['file']))
                    status = 'failed'
                else:
                    with open(self.nodes[self.nid]['input']['file']) as inp:
                        self.nodes[self.nid]['output'] = {'file':inp.read()}
        else:
            logging.info('No input defined')
        
        self.status = status
        self.utime = int(time.time())
        
        if callback:
            callback(self.nodes[self.nid])
        else:
            return self.nodes[self.nid]

class Choice(_TaskBase):
    
    def run_task(self, runner, callback=None, errorback=None):
        
        connections = self.children(return_nids=True)
        gofor = random.choice(connections)
        
        print("make a choice between: {0}, go for {1}".format(connections, gofor))
        for task in [t for t in connections if t != gofor]:
            self._full_graph.nodes[task]['status'] = 'disabled'
        
        self.nodes[self.nid]['output'] = self.nodes[self.nid].pop('input')
        self.status = 'failed'

class Collect(_TaskBase):
    
    def run_task(self, runner, callback=None, errorback=None):
        
        # Get all nodes connected to self. In the directed workflow graph these
        # are the ancestors
        ancestors = [nid for nid,adj in self.adjacency.items() if self.nid in adj]
        
        # Check if all the output of the ancestors is available
        task_ids = [self._full_graph.nodes[task]['task_id'] for task in ancestors]
        if all([tid in self.input for tid in task_ids]):
            logging.info('{0}: Output of {1} parent tasks available, continue'.format(self.task_name, len(ancestors)))
            self.nodes[self.nid]['output'] = self.input
            self.status = 'completed'

            callback(self.nodes[self.nid])
            
        else:
            logging.info('{0}: Not all output available yet'.format(self.task_name))


WORKFLOW_ORM = GraphORM(inherit=False)
WORKFLOW_ORM.map_node(StartTask, {'task_type':'Start'})
WORKFLOW_ORM.map_node(Task, {'task_type':'Task'})
WORKFLOW_ORM.map_node(Choice, {'task_type':'Choice'})
WORKFLOW_ORM.map_node(Collect, {'task_type':'Collect'})