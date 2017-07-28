from .workflow_runner import WorkflowRunner
from .workflow_spec import WorkflowSpec

# All in one Workflow class combining the functionality of the WorkflowRunner
# with the WorkflowSpec
Workflow = type('Workflow', (WorkflowRunner, WorkflowSpec), {})