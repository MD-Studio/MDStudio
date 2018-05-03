# -*- coding: utf-8 -*-

"""
file: dummy_task_runners

Dummy task runners to emulate various WAMP microservice response
constructs
"""

import time
import jsonschema


dummy_task_schema_input = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "id": "http://liestudio/schemas/dummy_task.json",
    "title": "Dummy input task",
    "description": "Dummy task input schema",
    "type": "object",
    "properties": {
        "dummy": {
            "description": "Output number from the dummy",
            "type": "integer"
        },
        "sleep": {
            "description": "Let the dummy task sleep for x seconds",
            "type": "integer",
            "default": 0
        },
        "add_number": {
            "description": "Add a number to the input integer",
            "type": "integer",
            "default": 0
        },
        "fail": {
            "description": "Instruct the dummy task to fail",
            "type": "boolean",
            "default": False
        },
        "crash": {
            "description": "Instruct the dummy task to crash",
            "type": "boolean",
            "default": False
        },
        "output_to_disk": {
            "description": "Write some output to disk",
            "type": "boolean",
            "default":False
        },
        "return_more": {
            "description": "Return a bunch of extra parameters",
            "type": "boolean",
            "default": False
        }
    },
    "required": ["dummy"]
}


dummy_task_schema_output = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "id": "http://liestudio/schemas/dummy_task.json",
    "title": "Dummy task output",
    "description": "Dummy task output schema",
    "type": "object",
    "properties": {
        "dummy": {
            "description": "Output number from the dummy",
            "type": "integer"
        }
    }
}


def calculate_accumulated_task_runtime(workflow):
    """
    Calculate cumultative task runtime
    """
    
    runtime = 0
    for tid,task in workflow.nodes.items():
        session = task.get('session')
        if session:
            runtime += (session.get('utime',0) - session.get('itime',0))
    
    return runtime


def task_runner(**kwargs):
    """
    Run a task based on the information in the task_data.
    Task_data is validated according to the JSON task schema
    """
    
    # The session is validated by the WAMP framework but the tasks specific
    # data will have to be validated by the task
    jsonschema.validate(kwargs, dummy_task_schema_input)

    # Simulate running the task
    time.sleep(kwargs.get('sleep',0))
    
    # Perform some calculations to simulate work
    # Add number to input
    output = kwargs['dummy'] + kwargs.get('add_number',0)

    # Create some local output on disk
    if kwargs.get('output_to_disk', False):
        with open('task_output.txt', 'w') as outf:
            outf.write('Output produced at: {0}\n\n'.format(time.time()))
            outf.write('Recieved input:\n')
            for i,p in kwargs.items():
                outf.write('{0} = {1}\n'.format(i,p))
            outf.write('\nReturned output:\n')
            outf.write('dummy = {0}\n'.format(output))

    # If fail that return None
    if kwargs.get('fail', False):
        return None

    # Crash the task by raising an exception with error message
    if kwargs.get('crash', False):
        raise Exception("Crashed task")

    # Return additional output
    rdict = {'dummy': output}
    if kwargs.get('return_more', False):
        rdict.update({'param1': True, 'param2': [1,2,3], 'param3': 5})

    return rdict


def reduce_function(**kwargs):
    """
    Dummy test reducer function taking the 'dummy' output from all previous
    tasks and adding them together
    """

    return {'dummy': sum(kwargs.get('dummy',[]))}
