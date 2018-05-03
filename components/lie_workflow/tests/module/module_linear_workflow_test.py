# -*- coding: utf-8 -*-

"""
file: module_linear_workflow_test.py

Unit tests construction and running the linear workflow:

    1 -- 2 -- 3 -- 4 -- 5
"""

import os
import unittest2
import time

from lie_workflow import Workflow, WorkflowSpec

currpath = os.path.dirname(__file__)
workflow_file_path = os.path.abspath(os.path.join(currpath, '../files/test-linear-workflow.jgf'))


class BaseWorkflowRunnerTests(object):

    def test1_initial_workflow_status(self):
        """
        Workflow has not been run before.
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertFalse(self.wf.has_failed)

    def test4_final_workflow_status(self):
        """
        Workflow should have been finished successfully
        """

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertFalse(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNotNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 8)
        self.assertLessEqual(self.wf.updatetime, self.wf.finishtime)

    def test5_final_workflow_output(self):
        """
        Test the output of the python function calculation
        """

        result = {}
        for task in self.wf.get_tasks():
            o = task.task_metadata.output_data.get(default={})
            result[task.key] = o.get('dummy')

        self.assertDictEqual(result, self.expected_output)


class TestBuildLinearWorkflow(unittest2.TestCase):
    """
    Build the linear workflow a shown in the file header
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup up workflow spec class
        """

        cls.spec = WorkflowSpec()

    def test1_set_project_meta(self):
        """
        Set project meta data
        """

        metadata = self.spec.workflow.query_nodes(key='project_metadata')
        self.assertFalse(metadata.empty())

        metadata.title.set('value', 'Simple linear workflow')
        metadata.description.set('value', 'Test a simple linear workflow of 5 blocking python tasks')

        self.assertTrue(all([n is not None for n in [metadata.title(), metadata.description()]]))

    def test2_add_methods(self):
        """
        Test adding 5 blocking Python tasks
        """

        for task in range(5):
            self.spec.add_task('test{0}'.format(task+1), task_type='BlockingPythonTask',
                               custom_func="dummy_task_runners.task_runner")

        self.assertEqual(len(self.spec), 5)

    def test3_add_connections(self):
        """
        Test connecting 5 tasks in a linear fashion
        """

        tasks = self.spec.get_tasks()
        for i in range(0, len(tasks), 1):
            connect = tasks[i:i+2]
            if len(connect) == 2:
                self.spec.connect_task(*[t.nid for t in connect])

    def test4_save_workflow(self):
        """
        Test save workflow to default jgf format
        """

        self.spec.save(path=workflow_file_path)
        self.assertTrue(os.path.exists(workflow_file_path))


class TestRunLinearWorkflowDefault(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': 7, u'test4': 10, u'test5': 11}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)


class TestRunLinearWorkflowFail(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow but instruct
    the python function to fail at task 'test3'
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': None, u'test4': None, u'test5': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            if task.key == 'test3':
                task.set_input(fail=True)

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

    def test4_final_workflow_status(self):
        """
        Workflow should have failed
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 5)

        self.assertEqual(self.wf.failed_tasks, [self.wf.workflow.query_nodes(key='test3')])


class TestRunLinearWorkflowCrash(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow but instruct
    the python function to crash at task 'test3'
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': None, u'test4': None, u'test5': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            if task.key == 'test3':
                task.set_input(crash=True)

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

    def test4_final_workflow_status(self):
        """
        Workflow should have failed
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 5)

        self.assertEqual(self.wf.failed_tasks, [self.wf.workflow.query_nodes(key='test3')])


class TestRunLinearWorkflowBreakpoint(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow but instruct
    the python function to pause at task 'test3' (breakpoint)
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': 7, u'test4': 10, u'test5': 11}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to pause at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            if task.key == 'test3':
                task.task_metadata.breakpoint.value = True

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow hits breakpoint
        while self.wf.is_running:
            time.sleep(1)

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)

        # Step the breakpoint
        bp = self.wf.active_breakpoints
        self.assertEqual(bp, [self.wf.workflow.query_nodes(key='test3')])
        self.wf.step_breakpoint(bp[0].nid)

        # Run the workflow
        self.wf.run(tid=bp[0].nid)

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

    def test4_final_workflow_status(self):
        """
        Workflow should have failed
        """

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertFalse(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNotNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 10)
        self.assertLessEqual(self.wf.updatetime, self.wf.finishtime)

        self.assertEqual(self.wf.active_breakpoints, [])


class TestRunLinearWorkflowRetrycount(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow but instruct
    the python function to fail at task 'test3' after trying 3 times
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': None, u'test4': None, u'test5': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3 but retry 3 times
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            if task.key == 'test3':
                task.task_metadata.retry_count.value = 3
                task.set_input(fail=True)

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

    def test4_final_workflow_status(self):
        """
        Workflow should have failed
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 9)

        bp = self.wf.workflow.query_nodes(key='test3')

        self.assertEqual(bp.task_metadata.retry_count(), 0)
        self.assertEqual(self.wf.failed_tasks, [bp])


class TestRunLinearWorkflowCancel(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the linear workflow build in TestBuildLinearWorkflow but cancel it
    at workflow task3
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': None, u'test4': None, u'test5': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildLinearWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Cancel the workflow at task3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 10, 3, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: cancel workflow after 5 seconds
        while self.wf.is_running:
            time.sleep(5)
            self.wf.cancel()

    def test4_final_workflow_status(self):
        """
        Workflow should have failed at task3
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertLessEqual(self.wf.runtime, 9)

        bp = self.wf.workflow.query_nodes(key='test3')
        self.assertTrue(bp.status == 'aborted')


class TestImportFinishedWorkflow(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Import a finished workflow and run it. Should check all steps but not rerun
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': 7, u'test4': 10, u'test5': 11}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        cls.wf = Workflow()
        cls.wf.load(os.path.abspath(os.path.join(currpath, '../files/test-linear-finished.jgf')))

    def test1_initial_workflow_status(self):
        """
        Workflow has not been run before.
        """

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertFalse(self.wf.has_failed)

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)


class TestImportUnfinishedWorkflow(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Import unfinished workflow and continue
    """

    expected_output = {u'test1': 4, u'test2': 6, u'test3': 7, u'test4': 10, u'test5': 11}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        cls.wf = Workflow()
        cls.wf.load(os.path.abspath(os.path.join(currpath, '../files/test-linear-unfinished.jgf')))

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)


class TestZcleanup(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Cleanup workflow files created by other tests
        """

        if os.path.exists(workflow_file_path):
            os.remove(workflow_file_path)

    def test_dummy(self):

        pass