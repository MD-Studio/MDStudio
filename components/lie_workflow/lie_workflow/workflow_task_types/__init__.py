# -*- coding: utf-8 -*-

"""
package: workflow_task_types

Collection of classes defining workflow task types
"""

from lie_graph.graph_orm import GraphORM
from lie_graph.graph_model_classes.model_user import User
from lie_graph.graph_model_classes.model_datetime import DateTime
from lie_graph.graph_model_classes.model_identifiers import UUID
from lie_graph.graph_model_classes.model_files import FilePath
from lie_graph.graph_io.io_jsonschema_format_drafts import StringType

from .task_python_type import PythonTask, BlockingPythonTask, LoadCustomFunc
from .task_wamp_type import WampTask

# Define the workflow Task ORM
WORKFLOW_ORM = GraphORM(inherit=False)
WORKFLOW_ORM.map_node(PythonTask, task_type='PythonTask')
WORKFLOW_ORM.map_node(BlockingPythonTask, task_type='BlockingPythonTask')
WORKFLOW_ORM.map_node(WampTask, task_type='WampTask')
WORKFLOW_ORM.map_node(User, key='user')
WORKFLOW_ORM.map_node(DateTime, format='date-time')
WORKFLOW_ORM.map_node(UUID, format='uuid')
WORKFLOW_ORM.map_node(LoadCustomFunc, key='custom_func')
WORKFLOW_ORM.map_node(StringType, key='custom_func')
WORKFLOW_ORM.map_node(StringType, key='status')
WORKFLOW_ORM.map_node(StringType, key='uri')
WORKFLOW_ORM.map_node(FilePath, key='project_dir')
WORKFLOW_ORM.map_node(FilePath, key='workdir')
