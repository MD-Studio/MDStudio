# -*- coding: utf-8 -*-

"""
file: dummy_task_runners

Dummy task runners to emulate various WAMP microservice response
constructs
"""

import os
import json
import logging
import time
import copy
import jsonschema

from lie_system import WAMPTaskMetaData
from lie_workflow import task_schema


def calculate_accumulated_task_runtime(workflow):
    """
    Calculate cumultative task runtime
    """
    
    runtime = 0
    for tid,task in workflow.nodes.items():
        runtime += (task.get('utime',0) - task.get('itime',0))
    
    return runtime
    
def task_runner(task_data):
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
    
    # Perform some calculations to simulate work
    # Add number to input
    inp = inp.get('dummy')
    if type(inp) == int:
        inp += conf.get('add_number',0)
    
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
    task_data['output'] = {'dummy': inp}
    task_data.update(session.dict())
    
    return task_data

def reduce_function(task_data):
    """
    Dummy test reducer function taking the 'dummy' output from all previous
    tasks and adding them together
    """
    
    total = 0
    for output in task_data:
        total += output.get('dummy',0)
    
    return {'dummy': total}
    