# -*- coding: utf-8 -*-

"""
file: module_test.py

Unit test the Task model API
"""

import os
import unittest2
import pkg_resources
import pytz

from datetime import datetime

from lie_graph.graph_io.io_jsonschema_format import read_json_schema
from lie_graph.graph_io.io_jsonschema_format_drafts import GraphValidationError

from lie_workflow.workflow_task_types import WORKFLOW_ORM

currpath = os.path.dirname(__file__)
    

class TestTaskObject(unittest2.TestCase):
    """
    Test creation and manipulation of Task objects using Task model API methods
    """

    task_schema = pkg_resources.resource_filename('lie_workflow', '/schemas/resources/task_template.json')

    def setUp(self):
        """
        Load a task specification from JSON Schema file
        """

        self.task_graph = read_json_schema(self.task_schema, exclude_args=['description'])
        self.task_graph.orm = WORKFLOW_ORM
        self.task = self.task_graph.get_root()

    def test_task_status(self):
        """
        Test task status attribute
        """

        # Default status equals 'ready'
        self.assertTrue(self.task.status.value, 'ready')

        self.task.status.set('value', 'running')
        self.assertTrue(self.task.status.value, 'running')

        # Set number of options to choose from
        self.assertRaises(GraphValidationError, self.task.status.set, 'value', 'unsupported')

    def test_task_datetime(self):
        """
        Test get/set of various date-time stamps
        """

        start_time = self.task.startedAtTime
        dt = datetime.now(tz=pytz.utc)
        start_time.set()

        self.assertEqual(start_time.get(), dt.replace(microsecond=(dt.microsecond // 1000) * 1000).isoformat())
        self.assertIsInstance(start_time.datetime(), datetime)
        self.assertIsInstance(start_time.get(), str)

        # Date-time parsing from string validation
        self.assertRaises(GraphValidationError, start_time.set, 'value', 'not a date-time string')

    def test_task_taskid(self):
        """
        Test get/set of unique task ID
        """

        uuid = self.task.task_id.create()
        self.task.task_id.set('value', uuid)

        self.assertEqual(self.task.task_id.value, uuid)

        # Basic UUID validation (regex)
        self.assertRaises(GraphValidationError, self.task.task_id.set, 'value', '74cf20d9-417c-11z8-acbc32aebef5')

    def test_task_retrycount(self):
        """
        Test get/set of task retry count
        """

        self.assertEqual(self.task.retry_count.value, 0)

        self.task.retry_count.value += 1
        self.assertEqual(self.task.retry_count.value, 1)