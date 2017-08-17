# -*- coding: utf-8 -*-

"""
file: module_test.py

Unit tests for a single branched workflow
"""

import os
import sys
import unittest2
import logging
import time

from   lie_workflow                import Workflow
from   dummy_task_runners          import task_runner, calculate_accumulated_task_runtime

currpath = os.path.dirname(__file__)
    

class TestBranchedWorkflow(unittest2.TestCase):
    """
    Test simple branched workflow
    """
    
    workflow_spec_path = os.path.abspath(os.path.join(currpath, '../files/branched-workflow-spec.json'))
    
    def setUp(self):
        """
        Load a simple branched workflow from a JSON specification
        """
        
        # Construct the workflow specification
        self.wf = Workflow()
        self.wf.task_runner = task_runner
        self.wf.load(self.workflow_spec_path)
        
        # Define dummy input the dummy_task_runner knows how to handle
        self.wf.input(dummy=1)

    def test_workflow_single_branched(self):
        """
        Test single branched workflow successful execution.
        With threaded tasks, the total workflow runtime is less than the
        accumulated task runtime.
        """
        
        self.wf.workflow.nodes[5]['input_data']['sleep'] = 4
        self.wf.workflow.nodes[7]['input_data']['sleep'] = 2
        
        # Run the workflow
        self.wf.run()

        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertListEqual(self.wf.output().keys(), [8,6])
        
        runtime = calculate_accumulated_task_runtime(self.wf.workflow)
        self.assertLess(self.wf.runtime(), runtime)
        self.assertEqual(self.wf.runtime(tid=5), 4)
        self.assertEqual(self.wf.runtime(tid=7), 2)
        
    def test_workflow_single_branched_blocking(self):
        """
        Test single branched workflow successful execution using BlockingTasks.
        With all tasks converted from threaded Task to BlockingTasks objects,
        the total workflow runtime equals the accumulated task runtime.
        """

        # Convert all Task types to BlockingTask
        for n,v in self.wf.workflow.nodes.items():
            if v['task_type'] == 'Task':
                v['task_type'] = 'BlockingTask'

        self.wf.workflow.nodes[5]['input_data']['sleep'] = 4
        self.wf.workflow.nodes[7]['input_data']['sleep'] = 2

        # Run the workflow
        self.wf.run()

        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertListEqual(self.wf.output().keys(), [8,6])

        runtime = calculate_accumulated_task_runtime(self.wf.workflow)
        self.assertEqual(self.wf.runtime(), runtime)
        self.assertEqual(self.wf.runtime(tid=5), 4)
        self.assertEqual(self.wf.runtime(tid=7), 2)

    def test_workflow_single_branched_fail(self):
        """
        Simulate a nicely failing task on one branch.
        Workflow should finish the other branch
        """

        self.wf.workflow.nodes[7]['input_data']['fail'] = True

        # Run the workflow
        self.wf.run()

        while self.wf.is_running:
            time.sleep(1)

        runtime = calculate_accumulated_task_runtime(self.wf.workflow)
        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.failed_task, 7)
        self.assertLess(self.wf.runtime(), runtime)
        self.assertEqual(self.wf.workflow.nodes[6]['output_data']['dummy'], 8)
        self.assertEqual(self.wf.get_task(8).status, 'ready')

    def test_workflow_single_branched_retrycount(self):
        """
        Test retry of failing nodes
        """

        # Set retrycount globally
        for task in self.wf.workflow.nodes:
            self.wf.workflow.nodes[task]['retry_count'] = 3

        # Instruct the runner to fail at node 7
        self.wf.workflow.nodes[7]['input_data']['fail'] = True
        self.wf.workflow.nodes[7]['input_data']['sleep'] = 2

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.workflow[7]['retry_count'], 0)
        self.assertEqual(self.wf.failed_task, 7)

        runtime = calculate_accumulated_task_runtime(self.wf.workflow)
        self.assertLess(runtime, self.wf.runtime())

    def test_workflow_single_branched_crash(self):
        """
        Simulate a failed workflow due to abruptly failed (crashed)
        task.
        """

        # Instruct the runner to fail at node 7
        self.wf.workflow.nodes[7]['input_data']['crash'] = True

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.failed_task, 7)

    def test_workflow_single_branched_breakpoint(self):
        """
        Simulate a breakpoint at node 7 and step over
        it manually to finish workflow
        """

        # Set a breakpoint at node 7
        self.wf.workflow.nodes[7]['breakpoint'] = True

        # Run the workflow
        self.wf.run()

        # Blocking: wait until the workflow hits an active breakpoint
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertEqual(self.wf.active_breakpoint, 7)

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

    def test_workflow_single_branched_cancel(self):
        """
        Simulate canceling the workflow after 5 seconds.
        That should leave nodes 6 and 8 to be canceled
        """

        # Run the workflow
        self.wf.run()

        while self.wf.is_running:
            time.sleep(5)
            self.wf.cancel()

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertListEqual([n for n,v in self.wf.workflow.nodes.items() if v['status'] == 'aborted'], [6,8])