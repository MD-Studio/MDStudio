# -*- coding: utf-8 -*-

"""
file: module_workflow_semantics_test.py

Unit tests naming and renaming of task parameters between tasks
"""

import os
import unittest2
import time

from lie_workflow import Workflow

currpath = os.path.dirname(__file__)


class TestInputOutputMapping(unittest2.TestCase):

    def setUp(self):
        """
        Build two task workflow
        """

        self.wf = Workflow()

        self.tid1 = self.wf.add_task('test1', custom_func="dummy_task_runners.task_runner")
        self.tid1.set_input(add_number=10, dummy=2)

        self.tid2 = self.wf.add_task('test2', custom_func="dummy_task_runners.task_runner")
        self.tid2.set_input(add_number=8)
        self.wf.connect_task(self.tid1.nid, self.tid2.nid, 'dummy')

    def test_run_default(self):
        """
        Test run workflow storing output of all tasks
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        # Check existence of project dir, tasks dirs and workflow graph file.
        expected = {'test1': 12, 'test2': 20}
        for task in self.wf.get_tasks():
            self.assertEqual(task.get_output().get('dummy'), expected[task.key])

    def test_run_keyword_mapping(self):
        """
        Test run workflow storing output of all tasks
        """

        # Change mapping
        self.tid1.set_input(return_more=True)
        edge = self.wf.workflow.getedges((self.tid1.nid, self.tid2.nid))
        edge.set('data_mapping', {'param3':'dummy'})

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        # Check existence of project dir, tasks dirs and workflow graph file.
        expected = {'test1': 12, 'test2': 13}
        for task in self.wf.get_tasks():
            self.assertEqual(task.get_output().get('dummy'), expected[task.key])