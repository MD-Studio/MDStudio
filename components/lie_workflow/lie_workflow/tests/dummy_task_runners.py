# -*- coding: utf-8 -*-

"""
file: dummy_task_runners

Dummy task runners to emulate various WAMP microservice response
constructs
"""

import logging
import time
import copy
import jsonschema

from   lie_componentbase                 import WAMPTaskMetaData
from   lie_workflow.task_metadata import task_schema

class TaskRunner(object):
    
    def task(self, task_data):
        """
        Run a task based on the information in the task_data.
        Task_data is validated accoridng to the JSON task schema
        """
        
        jsonschema.validate(task_data, task_schema)
        
        # Retrieve the WAMP session information
        session = WAMPTaskMetaData(metadata=task_data.get('session'))
        session._metadata['itime'] = int(time.time())
        
        # Prepaire the input to the task
        inp = task_data.get('input')
        
        # Get the task configuration
        conf = task_data.get('configuration', {})
        
        # Simulate running the task
        time.sleep(conf.get('sleep',0))
        
        # Fail or not
        if conf.get('fail', False):
            session.status = 'failed'
        else:
            session.status = 'completed'
        session._update_time(time_stamp='utime')
        
        # Crash?
        if conf.get('crash', False):
            raise Exception("Crashed task")
        
        # Prepaire the output
        session._metadata['utime'] = int(time.time())
        task_data['output'] = {session['task_id']: task_data['task_name']}
        task_data.update(session.dict())
        
        return task_data