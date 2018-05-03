# -*- coding: utf-8 -*-

"""
file: module_branched_workflow_test.py

Unit tests construction and running the branched workflow:

                6 -- 7 -- 8
               /
    1 -- 2 -- 3 -- 4 -- 5
                   \
                    9 -- 10
"""

import os
import unittest2
import time

from lie_workflow import Workflow, WorkflowSpec

currpath = os.path.dirname(__file__)
workflow_file_path = os.path.abspath(os.path.join(currpath, '../files/test-branched-workflow.jgf'))


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
        self.assertTrue(8 < self.wf.runtime < 12)
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


class TestBuildBranchedWorkflow(unittest2.TestCase):
    """
    Build the branched workflow a shown in the file header using the default
    threader PythonTask runner
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

        metadata.title.set('value', 'Simple branched workflow')
        metadata.description.set('value', 'Test a simple branched workflow of 10 threaded python tasks')

        self.assertTrue(all([n is not None for n in [metadata.title(), metadata.description()]]))

    def test2_add_methods(self):
        """
        Test adding 10 blocking python tasks
        """

        for task in range(10):
            self.spec.add_task('test{0}'.format(task+1),
                               custom_func="dummy_task_runners.task_runner")

        self.assertEqual(len(self.spec), 10)

    def test3_add_connections(self):
        """
        Test connecting 10 tasks in a branched fashion
        """

        edges = ((1, 2), (2, 3), (3, 4), (4, 5), (3, 6), (6, 7), (7, 8), (4, 9), (9, 10))
        tasks = dict([(i, t.nid) for i, t in enumerate(self.spec.get_tasks(), start=1)])

        for edge in edges:
            self.spec.connect_task(tasks[edge[0]], tasks[edge[1]])

        self.assertTrue(len(self.spec.workflow.adjacency[tasks[3]]), 3)
        self.assertTrue(len(self.spec.workflow.adjacency[tasks[4]]), 3)

    def test4_save_workflow(self):
        """
        Test save workflow to default jgf format
        """

        self.spec.save(path=workflow_file_path)
        self.assertTrue(os.path.exists(workflow_file_path))


class TestRunBranchedWorkflowDefault(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': 11, u'test4': 10, u'test7': 10, u'test6': 9,
                       u'test9': 12, u'test8': 11, u'test10': 13}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
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


class TestRunBranchedWorkflowBlocking(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but replacing
    the threaded PythonTask for a BlockingPythonTask
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': 11, u'test4': 10, u'test7': 10, u'test6': 9,
                       u'test9': 12, u'test8': 11, u'test10': 13}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            # Switch task type from BlockingPythonTask to PythonTask
            task.task_type = 'BlockingPythonTask'

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
        Workflow should have been finished successfully
        """

        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)
        self.assertFalse(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNotNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)
        self.assertTrue(14 < self.wf.runtime < 17)
        self.assertLessEqual(self.wf.updatetime, self.wf.finishtime)


class TestRunLinearWorkflowFail(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but instruct
    the python function to fail at task 'test4'
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': None, u'test4': None, u'test7': 10, u'test6': 9,
                       u'test9': None, u'test8': 11, u'test10': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            task.set_input(add_number=sleep_times[i], sleep=sleep_times[i])

            if task.key == 'test4':
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
        Workflow should have failed at test4 but the branch leading to test8
        should have finished normally.
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)

        completed = [t.key for t in self.wf.get_tasks() if t.status == 'completed']
        notcompleted = [t.key for t in self.wf.get_tasks() if t.status != 'completed']

        self.assertItemsEqual(completed, ['test1', 'test2', 'test3', 'test6', 'test7', 'test8'])
        self.assertItemsEqual(notcompleted, ['test4', 'test5', 'test9', 'test10'])
        self.assertEqual(self.wf.failed_tasks, [self.wf.workflow.query_nodes(key='test4')])


class TestRunLinearWorkflowCrash(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but instruct
    the python function to crash at task 'test4'
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': None, u'test4': None, u'test7': 10, u'test6': 9,
                       u'test9': None, u'test8': 11, u'test10': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            self.wf.input(task.nid, add_number=sleep_times[i],
                          sleep=sleep_times[i])

            if task.key == 'test4':
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
        Workflow should have failed at test4 but the branch leading to test8
        should have finished normally.
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)

        completed = [t.key for t in self.wf.get_tasks() if t.status == 'completed']
        notcompleted = [t.key for t in self.wf.get_tasks() if t.status != 'completed']

        self.assertItemsEqual(completed, ['test1', 'test2', 'test3', 'test6', 'test7', 'test8'])
        self.assertItemsEqual(notcompleted, ['test4', 'test5', 'test9', 'test10'])
        self.assertEqual(self.wf.failed_tasks, [self.wf.workflow.query_nodes(key='test4')])


class TestRunBranchedWorkflowBreakpoint(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but instruct
    the python function to pause at task 'test4' (breakpoint)
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': 11, u'test4': 10, u'test7': 10, u'test6': 9,
                       u'test9': 12, u'test8': 11, u'test10': 13}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to pause at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            self.wf.input(task.nid, add_number=sleep_times[i],
                          sleep=sleep_times[i])

            if task.key == 'test4':
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

        # Tasks upto task8 should have finished normally
        self.assertEquals(self.wf.workflow.query_nodes(key='test8').status, 'completed')

        # Step the breakpoint
        bp = self.wf.active_breakpoints
        self.assertEqual(bp, [self.wf.workflow.query_nodes(key='test4')])
        self.wf.step_breakpoint(bp[0].nid)

        # Run the workflow
        self.wf.run(tid=bp[0].nid)

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(1)

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


class TestRunLinearWorkflowRetrycount(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but instruct
    the python function to fail at task 'test4' after trying 3 times
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': None, u'test4': None, u'test7': 10, u'test6': 9,
                       u'test9': None, u'test8': 11, u'test10': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            self.wf.input(task.nid, add_number=sleep_times[i],
                          sleep=sleep_times[i])

            if task.key == 'test4':
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
        Workflow should have failed at test4 but the branch leading to test8
        should have finished normally.
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)

        bp = self.wf.workflow.query_nodes(key='test4')

        self.assertEqual(bp.task_metadata.retry_count(), 0)
        self.assertEqual(self.wf.failed_tasks, [bp])

        completed = [t.key for t in self.wf.get_tasks() if t.status == 'completed']
        notcompleted = [t.key for t in self.wf.get_tasks() if t.status != 'completed']

        self.assertItemsEqual(completed, ['test1', 'test2', 'test3', 'test6', 'test7', 'test8'])
        self.assertItemsEqual(notcompleted, ['test4', 'test5', 'test9', 'test10'])


class TestRunLinearWorkflowCancel(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Run the branched workflow build in TestBuildBranchedWorkflow but instruct
    the python function to fail at task 'test4' after trying 3 times
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': None, u'test4': None, u'test7': None,
                       u'test6': None, u'test9': None, u'test8': None, u'test10': None}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        if not os.path.exists(workflow_file_path):
            raise unittest2.SkipTest('TestBuildBranchedWorkflow failed to build workflow')

        cls.wf = Workflow()
        cls.wf.load(workflow_file_path)

    def test2_define_input(self):
        """
        Set initial input to the workflow
        Instruct the runner to fail at node 3
        """

        self.wf.input(self.wf.workflow.root, dummy=3)
        sleep_times = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]
        for i, task in enumerate(self.wf.get_tasks()):
            self.wf.input(task.nid, add_number=sleep_times[i],
                          sleep=sleep_times[i])

    def test3_run_workflow(self):
        """
        Test running the workflow
        """

        # Run the workflow
        self.wf.run()

        # Blocking: wait until workflow is no longer running
        while self.wf.is_running:
            time.sleep(6)
            self.wf.cancel()

    def test4_final_workflow_status(self):
        """
        Workflow should have failed at test4 but the branch leading to test8
        should have finished normally.
        """

        self.assertFalse(self.wf.is_running)
        self.assertFalse(self.wf.is_completed)
        self.assertTrue(self.wf.has_failed)

        self.assertIsNotNone(self.wf.starttime)
        self.assertIsNone(self.wf.finishtime)
        self.assertIsNotNone(self.wf.updatetime)

        aborted = [t.key for t in self.wf.get_tasks() if t.status == 'aborted']
        completed = [t.key for t in self.wf.get_tasks() if t.status == 'completed']

        self.assertItemsEqual(aborted, ['test4', 'test6'])
        self.assertItemsEqual(completed, ['test1', 'test2', 'test3'])


class TestImportFinishedWorkflow(BaseWorkflowRunnerTests, unittest2.TestCase):
    """
    Import a finished workflow and run it. Should check all steps but not rerun
    """

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': 11, u'test4': 10, u'test7': 10, u'test6': 9,
                       u'test9': 12, u'test8': 11, u'test10': 13}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        cls.wf = Workflow()
        cls.wf.load(os.path.abspath(os.path.join(currpath, '../files/test-branched-finished.jgf')))

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

    expected_output = {u'test1': 4, u'test3': 7, u'test2': 6, u'test5': 11, u'test4': 10, u'test7': 10, u'test6': 9,
                       u'test9': 12, u'test8': 11, u'test10': 13}

    @classmethod
    def setUpClass(cls):
        """
        Load previously created linear workflow spec file
        """

        cls.wf = Workflow()
        cls.wf.load(os.path.abspath(os.path.join(currpath, '../files/test-branched-unfinished.jgf')))

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