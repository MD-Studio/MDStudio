# -*- coding: utf-8 -*-

"""
file: module_workflowspec_test.py

Unit tests for the WorkflowSpec class
"""

import os
import json
import unittest2

from jsonschema.exceptions import ValidationError

from lie_workflow import WorkflowSpec
from lie_workflow.common import WorkflowError

currpath = os.path.dirname(__file__)


class TestWorkflowSpec(unittest2.TestCase):
    """
    Test WorkflowSpec class
    """
    
    tempfiles = []
    
    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the working directory
        """

        for temp in self.tempfiles:
            if os.path.exists(temp):
                os.remove(temp)
    
    def test_new_default(self):
        """
        Create empty workflow from default workflow JSON schema included in
        the module.
        Empty workflow has one task (node) of type Start that is root
        """
        
        spec = WorkflowSpec()
        
        self.assertEqual(spec.workflow.root, 1)
        self.assertEqual(spec.workflow[1]['task_type'], 'Start')
        self.assertEqual(len(spec.workflow), 1)
        
        self.assertTrue(hasattr(spec.workflow, 'title'))
        self.assertTrue(hasattr(spec.workflow, 'description'))
        
    def test_load_valid_spec(self):
        """
        Load a predefined and valid workflow specification from JSON file.
        """
        
        spec = WorkflowSpec()
        spec.load(os.path.join(currpath, '../files/linear-workflow-finished.json'))

        self.assertEqual(spec.workflow.root, 1)
        self.assertEqual(spec.workflow[1]['task_type'], 'Start')
        self.assertEqual(len(spec.workflow), 6)
        
        self.assertTrue(all([len(edge) == 2 for edge in spec.workflow.edges]))
    
    def test_load_invalid_spec(self):
        """
        Load a predefined invalid workflow specification from JSON file.
        This workflow is build as undirected graph that should be directed.
        The root node is not of type 'Start'.
        """
        
        invalid_workflow = None
        with open(os.path.join(currpath, '../files/linear-workflow-invalid.json')) as wf:
            invalid_workflow = json.load(wf)
        
        spec = WorkflowSpec()
        self.assertRaises(ValidationError, spec.load, invalid_workflow)
        
        # Fix the error and try again, fails because Start node not defined
        invalid_workflow['graph']['is_directed'] = True
        self.assertRaises(WorkflowError, spec.load, invalid_workflow)
    
    def test_save_spec(self):
        """
        Save a constructed workflow specification to file and load it again
        """
        
        spec = WorkflowSpec()

        for task in range(5):
            spec.add_task('task{0}'.format(task+1), configuration={'sleep':0})
            if task == 0:
                spec.connect_task('start', 'task1')
            else:
                spec.connect_task('task{0}'.format(task), 'task{0}'.format(task+1))

        # Set some metadata
        spec.workflow.title = 'Test project'

        path = os.path.abspath(os.path.join(currpath, '../files/test_workflow_save.json'))
        self.tempfiles.append(path)
        spec.save(path=path)
        
        self.assertTrue(os.path.exists(path))
        
        # Load saved spec again
        spec.load(path)
        
        self.assertEqual(spec.workflow.root, 1)
        self.assertEqual(spec.workflow[1]['task_type'], 'Start')
        self.assertEqual(len(spec.workflow), 6)
        
        self.assertTrue(all([len(edge) == 2 for edge in spec.workflow.edges]))
    
    def test_query_finished_spec(self):
        """
        Query for global and local metadata on a finished workflow
        """
        
        spec = WorkflowSpec()
        spec.load(os.path.join(currpath, '../files/linear-workflow-finished.json'))
        
        # Query local metadata
        task2 = spec.get_task('task1')
        self.assertEqual(task2.utime, 1493819368)
        self.assertEqual(task2.status, 'completed')
        self.assertEqual(task2.utime - task2.itime, 1)
        
    def test_build_linear_spec(self):
        """
        Construct a simple linear workflow specification of 6 nodes
        """
        
        spec = WorkflowSpec()
        
        for task in range(5):
            spec.add_task('task{0}'.format(task+1), configuration={'sleep':0})
            if task == 0:
                spec.connect_task('start', 'task1')
            else:
                spec.connect_task('task{0}'.format(task), 'task{0}'.format(task+1))

        # Set some metadata
        spec.workflow.title = 'Test project'
                
    def test_build_branched_spec(self):
        """
        Construct a branched workflow specification that behaves as a map-reduce
        style workflow.
        """
        
        spec = WorkflowSpec()

        # Add task nodes
        for task in range(9):
            spec.add_task('task{0}'.format(task+1), configuration={'sleep':0})
        spec.workflow.nodes[9]['task_type'] = 'Collect'

        # Connect tasks
        connections = (('start','task1'), ('task1','task2'), ('task2','task3'),
                       ('task3','task4'), ('task3','task6'), ('task4','task5'),
                       ('task6','task7'), ('task7','task8'), ('task5','task8'),
                       ('task8','task9'))
        for pair in connections:
            spec.connect_task(*pair)

        # Set some metadata
        spec.workflow.title = 'Map-reduce project'
       
        maptask = [n for n in spec.workflow.nodes if len(spec.workflow.adjacency[n]) > 1 and spec.workflow.nodes[n]['task_type'] == 'Task']
        redtask = [n for n in spec.workflow.nodes if spec.workflow.nodes[n]['task_type'] == 'Collect']
        self.assertListEqual(maptask, [4])
        self.assertListEqual(redtask, [9])
    
    def test_orm_spec(self):
        """
        Test Graph ORM functionality
        """
        
        spec = WorkflowSpec()
        self.assertRaises(AssertionError, spec.add_task, 'boogie', task_type='not_exist')