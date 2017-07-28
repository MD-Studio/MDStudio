# -*- coding: utf-8 -*-

"""
file: module_test.py

Unit tests for the Workflow class
"""

import os
import sys
import unittest2
import logging
import time

from   lie_workflow                import Workflow
from   dummy_task_runners          import task_runner

currpath = os.path.dirname(__file__)


class TestLinearWorkflow(unittest2.TestCase):
    """
    Test workflow specification construction
    """
    
    workflow_spec_path = os.path.abspath(os.path.join(currpath, '../files/linear-workflow-spec.json'))
    
    def setUp(self):
        """
        Build a simple linear workflow of 5 nodes
        """
        
        # Construct the workflow specification
        self.wf = Workflow()
        self.wf.task_runner = task_runner
        self.wf.load(self.workflow_spec_path)
    
    def tester(self):
        
        # Define some input
        self.wf.input(dummy=1)
        
        for n,v in self.wf.workflow.nodes.items():
            if "configuration" in v and v["configuration"].get("sleep",0) != 3:
                v["configuration"]["sleep"] = 1
        
        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            a = self.wf.active_tasks
            print(a, self.wf.workflow_thread.is_alive())
            if 4 in a:
                self.wf.cancel()
            time.sleep(0.1)
        
        time.sleep(5)
        print(self.wf.summary())
        print(self.wf.workflow_thread.is_alive())
    
    # def test_workflow_simple_linear(self):
    #     """
    #     Run the workflow from start till finish.
    #     """
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     # Blocking: wait until workflow is no longer running
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertTrue(self.wf.is_completed)
    #     self.assertEqual(self.wf.runtime, 3)
    #
    # def test_workflow_simple_linear_fail(self):
    #     """
    #     Simulate a nicely failing task.
    #     Nicely failed returns 'failed' status.
    #     """
    #
    #     # Instruct the runner to fail at node 3
    #     self.wf.workflow.nodes[3]['configuration']['fail'] = True
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     # Blocking: wait until workflow is no longer running
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertFalse(self.wf.is_completed)
    #     self.assertEqual(self.wf.failed_task, 3)
    #
    # def test_workflow_simple_linear_retrycount(self):
    #     """
    #     Test retry of failing nodes
    #     """
    #
    #     # Set retrycount globally
    #     for task in self.wf.workflow.nodes:
    #         self.wf.workflow.nodes[task]['retry_count'] = 3
    #
    #     # Instruct the runner to fail at node 3
    #     self.wf.workflow.nodes[3]['configuration']['fail'] = True
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     # Blocking: wait until workflow is no longer running
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertFalse(self.wf.is_completed)
    #     self.assertEqual(self.wf.workflow[3]['retry_count'], 0)
    #     self.assertEqual(self.wf.failed_task, 3)
    #
    # def test_workflow_simple_linear_crash(self):
    #     """
    #     Simulate a failed workflow due to abruptly failed (crashed)
    #     task.
    #     """
    #
    #     # Instruct the runner to fail at node 3
    #     self.wf.workflow.nodes[3]['configuration']['crash'] = True
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     # Blocking: wait until workflow is no longer running
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertFalse(self.wf.is_completed)
    #     self.assertEqual(self.wf.failed_task, 3)
    #
    # def test_workflow_simple_linear_breakpoint(self):
    #     """
    #     Simulate a breakpoint at node 3 and step over
    #     it manually to finish workflow
    #     """
    #
    #     # Set a breakpoint at node 3
    #     self.wf.workflow.nodes[3]['breakpoint'] = True
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     # Blocking: wait until workflow is no longer running (breakpoint)
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertFalse(self.wf.is_completed)
    #     self.assertEqual(self.wf.active_breakpoint, 3)
    #
    #     # Step the breakpoint
    #     bp = self.wf.active_breakpoint
    #     self.wf.step_breakpoint(bp)
    #
    #     # Run the workflow
    #     self.wf.run(tid=bp+1)
    #
    #     # Blocking: wait until workflow is no longer running
    #     while self.wf.is_running:
    #         time.sleep(1)
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertTrue(self.wf.is_completed)
    #     self.assertIsNone(self.wf.active_breakpoint)
    #
    # def test_workflow_simple_linear_cancel(self):
    #     """
    #     Simulate canceling the workflow at node 3
    #     """
    #
    #     # Set a breakpoint at node 3
    #     self.wf.workflow.nodes[3]['configuration']['sleep'] = 10
    #
    #     # Define some input
    #     self.wf.input(dummy='data_placeholder')
    #
    #     # Run the workflow
    #     self.wf.run()
    #
    #     while self.wf.is_running:
    #         time.sleep(5)
    #         self.wf.cancel()
    #
    #     self.assertFalse(self.wf.is_running)
    #     self.assertFalse(self.wf.is_completed)
    #     self.assertEqual(self.wf.workflow.nodes[3]['status'],'aborted')
    #
