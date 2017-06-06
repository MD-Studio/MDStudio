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

# class TestBranchedWorkflow(unittest2.TestCase):
#     """
#     Test workflow specification construction
#     """
#
#     def setUp(self):
#         """
#         Build a single branched workflow.
#         """
#
#         # Construct the workflow specification
#         self.wf = Workflow()
#         self.wf.task_runner = TaskRunner()
#
#         # Add task nodes
#         for task in range(7):
#             self.wf.add_task('task{0}'.format(task+1), configuration={'sleep':0})
#
#         # Connect tasks
#         connections = (('start','task1'), ('task1','task2'), ('task2','task3'),
#                        ('task3','task4'), ('task3','task6'), ('task4','task5'),
#                        ('task6','task7'))
#         for pair in connections:
#             self.wf.connect_task(*pair)
#
#     def test_single_branched_successfull(self):
#         """
#         Test single branched workflow successful execution
#         """
#
#         self.wf.workflow.nodes[5]['configuration']['sleep'] = 6
#         self.wf.workflow.nodes[7]['configuration']['sleep'] = 5
#
#         # Define some input
#         self.wf.input(dummy='data_placeholder')
#
#         # Run the workflow
#         self.wf.run(threaded=True)
#
#         while self.wf.is_running:
#             time.sleep(1)
#
#         self.assertFalse(self.wf.is_running)
#         self.assertTrue(self.wf.is_completed)
#         self.assertListEqual(self.wf.output().keys(), ['task5','task7'])
#
#     def test_single_branched_failed(self):
#         """
#         Test single branched workflow failed at task 6
#         """
#
#         # Instruct the runner to fail at node 3
#         self.wf.workflow.nodes[6]['configuration']['fail'] = True
#
#         # Define some input
#         self.wf.input(dummy='data_placeholder')
#
#         # Run the workflow
#         self.wf.run(threaded=True)
#
#         while self.wf.is_running:
#             time.sleep(1)
#
#         self.assertFalse(self.wf.is_running)
#         self.assertFalse(self.wf.is_completed)
#         self.assertListEqual(self.wf.output().keys(), ['task7'])

class TestMapReduceWorkflow(unittest2.TestCase):
    """
    Run a Map-Reduce style workflow testing default mapping function of
    the workflow runner and output gathering function of a special
    Reduce task type.
    """

    def setUp(self):
        """
        Build a single map reduce workflow
        """

        # Construct the workflow specification
        self.wf = Workflow()
        self.wf.task_runner = TaskRunner()

        # Add task nodes
        for task in range(9):
            self.wf.add_task('task{0}'.format(task+1), configuration={'sleep':0})
        self.wf.workflow.nodes[9]['task_type'] = 'Collect'

        # Connect tasks
        connections = (('start','task1'), ('task1','task2'), ('task2','task3'),
                       ('task3','task4'), ('task3','task6'), ('task4','task5'),
                       ('task6','task7'), ('task7','task8'), ('task5','task8'),
                       ('task8','task9'))
        for pair in connections:
            self.wf.connect_task(*pair)

    def test_mapreduce_successfull(self):
        """
        Test single branched workflow successful execution
        """

        # Define some input
        self.wf.input(dummy='data_placeholder')

        # Run the workflow
        self.wf.run(threaded=True)
        
        while self.wf.is_running:
            time.sleep(1)
            
        self.assertFalse(self.wf.is_running)
        self.assertTrue(self.wf.is_completed)

        print(write_json(self.wf.workflow))
