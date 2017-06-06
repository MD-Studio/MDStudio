# -*- coding: utf-8 -*-

"""
Workflow task JSON schema.

The `task_schema` describes the data structure of LIEStudio workflow task.

A default task contains:

* Task metadata that are used by the workflow engine to execute a workflow.
  These include the overal status of a task, retry count upon failure, 
  breakpoints and rather the task is currently active or not.
* Configuration is an object (dictionary in Python) that holds the
  configuration of the task to be excecuted as key/value pairs.
* Input is a mixed object that describes the data used as input to the task
* Output is a mized object that will hold the data that i returned by a task.
"""

task_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "id": "http://liestudio/schemas/workflowtask.json",
    "title": "Task",
    "description": "A default LIEStudio workflow task",
    "type": "object",
    "properties": {
        "active": {
            "description": "Is the current task active or not",
            "type": "boolean",
            "default": False
        },
        "breakpoint": {
            "description": "Add a breakpoint for the task. The workflow will only continue if explicitly instructed",
            "type": "boolean",
            "default": False
        },
        "configuration": {
            "description": "Configuration key/value pairs for the task",
            "type": "object",
            "default": {}
        },
        "input": {
            "description": "Input for the task",
            "type": "object"    
        },
        "output": {
            "description": "Output returned by the task",
            "type": "object"    
        },
        "replace_output": {
            "description": "Number of times the task should be resubmitted when it failed",
            "type": "boolean",
            "default": False
        },
        "retry_count": {
            "description": "Number of times the task should be resubmitted when it failed",
            "type": "integer",
            "default": 0
        },
        "status": {
            "description": "The status of the current task",
            "type": "string",
            "default": "ready",
            "enum": ["ready","submitted","running","failed","aborted","completed","deactivated"]
        },
        "task_id": {
            "type": "string",
            "description": "Unique ID used to identify the task in the system"
        },
        "uri": {
            "type": "string",
            "description": "LIEStudio microservice method uri",
            "pattern": "^\\w+(\\.\\w+)*$",
            "default": 'liestudio.default.task'
        },
    },
    "required": ["active", "breakpoint", "retry_count", "status", "uri", "configuration"]
}