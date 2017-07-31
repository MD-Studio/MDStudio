import os
import json

from .workflow_runner import WorkflowRunner
from .workflow_spec import WorkflowSpec

# All in one Workflow class combining the functionality of the WorkflowRunner
# with the WorkflowSpec
Workflow = type('Workflow', (WorkflowRunner, WorkflowSpec), {})

# Load default JSON task schema and workflow schema from file
TASK_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'task_schema.json')
task_schema = json.load(open(TASK_SCHEMA_PATH))