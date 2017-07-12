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

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

from   lie_graph.io.io_json_format import write_json
from   lie_workflow                import Workflow

from   dummy_task_runners          import TaskRunner

class TestWorkflow(unittest2.TestCase):
    """
    Test workflow specification construction
    """
    
    input_file_path = os.path.join(currpath, 'files/linear-workflow-finished.json')
    
    def setUp(self):
        """
        Build a simple linear workflow of 5 nodes
        """
        
        # Construct the workflow specification
        self.wf = Workflow()
        self.wf.task_runner = TaskRunner()
        
        for task in range(5):
            self.wf.add_task('task{0}'.format(task+1), configuration={'sleep':0})
            if task == 0:
                self.wf.connect_task('start', 'task1')
            else:
                self.wf.connect_task('task{0}'.format(task), 'task{0}'.format(task+1))
        
        # Set some metadata
        self.wf.workflow.nodes[1]['project_title'] = 'Test project'
        
    def test_workflow_simple_linear(self):
        """
        Run the workflow from start till finish.
        """
        
        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        
        print(write_json(self.wf.workflow))
        
    def test_workflow_simple_linear_fail(self):
        """
        Simulate a nicely failing task.
        Nicely failed returns 'failed' status.
        """

        # Instruct the runner to fail at node 3
        self.wf.workflow.nodes[3]['configuration']['fail'] = True

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()
        
        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.failed_task, 3)
    
    def test_workflow_simple_linear_retrycount(self):
        """
        Test retry of failing nodes
        """
        
        # Set retrycount globally
        for task in self.wf.workflow.nodes:
            self.wf.workflow.nodes[task]['retry_count'] = 3

        # Instruct the runner to fail at node 3
        self.wf.workflow.nodes[3]['configuration']['fail'] = True

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()
        
        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.workflow[3]['retry_count'], 0)
        self.assertEqual(self.wf.failed_task, 3)
        
    def test_workflow_simple_linear_crash(self):
        """
        Simulate a failed workflow due to abruptly failed (crashed)
        task.
        """

        # Instruct the runner to fail at node 3
        self.wf.workflow.nodes[3]['configuration']['crash'] = True

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()
        
        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.failed_task, 3)

    def test_workflow_simple_linear_breakpoint(self):
        """
        Simulate a breakpoint at node 3 and step over
        it manually to finish workflow
        """

        # Set a breakpoint at node 3
        self.wf.workflow.nodes[3]['breakpoint'] = True

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()
        
        # Blocking: wait until workflow is no longer running (breakpoint)
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.active_breakpoint, 3)

        # Step the breakpoint
        bp = self.wf.active_breakpoint
        self.wf.step_breakpoint(bp)
        
        # Run the workflow
        self.wf.run(tid=bp+1)

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertIsNone(self.wf.active_breakpoint)
        
    def test_workflow_simple_linear_cancel(self):
        """
        Simulate canceling the workflow at node 3
        """

        # Set a breakpoint at node 3
        self.wf.workflow.nodes[3]['configuration']['sleep'] = 10

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run()

        while self.wf.is_running:
            time.sleep(5)
            self.wf.cancel()
        
        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.workflow.nodes[3]['status'],'aborted')

