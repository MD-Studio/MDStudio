# -*- coding: utf-8 -*-

"""
file: module_workflowspec_test.py

Unit tests for the WorkflowSpec class
"""

import os
import json
import jsonschema
import unittest2

from lie_graph.graph_io.io_dict_format import write_dict

from lie_workflow import WorkflowSpec
from lie_workflow.workflow_common import WorkflowError
from lie_workflow.workflow_spec import workflow_metadata_template

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
        Test creation of new empty workflow based on JSON Schema.
        """

        spec = WorkflowSpec()

        self.assertEqual(spec.workflow.root, 1)

        # Test meta data
        metadata = spec.workflow.query_nodes(key='project_metadata')
        self.assertFalse(metadata.empty())
        self.assertTrue(metadata.parent().empty())  # Metadata is not rooted.
        self.assertItemsEqual(metadata.children().keys(), [u'update_time', u'description', u'title', u'finish_time',
                                                           u'start_time', u'create_time', u'user', u'version',
                                                           u'project_dir'])

        # Test schema, should validate OK
        schema = json.load(open(workflow_metadata_template))
        self.assertIsNone(jsonschema.validate(write_dict(metadata), schema))

    def test_add_task_unsupported(self):
        """
        Test 'add_task' with task type not loaded in the ORM
        """

        spec = WorkflowSpec()
        self.assertRaises(WorkflowError, spec.add_task, 'test', task_type='Unsupported')


    def test_connect_task(self):
        """
        Test connection of tasks
        """

        spec = WorkflowSpec()

        # Add 2 default tasks and connect
        for task in range(3):
            t = spec.add_task(task_name='task{0}'.format(task+1))
            if task != 0:
                spec.connect_task(spec.workflow.root, t.nid)

    def test_save_spec(self):
        """
        Save a constructed workflow specification to file and load it again
        """

        spec = WorkflowSpec()

        # Add 5 default tasks
        for task in range(5):
            t = spec.add_task('task{0}'.format(task+1))
            if task == 0:
                spec.connect_task(1, t.nid)
            else:
                spec.connect_task(t.nid-1, t.nid)

        # Set some metadata
        metadata = spec.workflow.query_nodes(key='project_metadata')
        metadata.title.value = 'Test project'

        path = os.path.abspath(os.path.join(currpath, '../files/test_workflow_save.jgf'))
        self.tempfiles.append(path)
        spec.save(path=path)

        self.assertTrue(os.path.exists(path))

        # Load saved spec again
        spec.load(path)

        self.assertEqual(spec.workflow.root, 11)
        self.assertEqual(spec.workflow[spec.workflow.root]['task_type'], 'PythonTask')
        self.assertEqual(len(spec.workflow.query_nodes(task_type='PythonTask')), 5)

    # def test_load_valid_spec(self):
    #     """
    #     Load a predefined and valid workflow specification from JSON file.
    #     """
    #
    #     spec = WorkflowSpec()
    #     spec.load(os.path.join(currpath, '../files/linear-workflow-finished.jgf'))
    #
    #     self.assertEqual(spec.workflow.root, 1)
    #     self.assertEqual(spec.workflow[1]['task_type'], 'Start')
    #     self.assertEqual(len(spec.workflow), 6)

    # def test_load_invalid_spec(self):
    #     """
    #     Load a predefined invalid workflow specification from JSON file.
    #     This workflow is build as undirected graph that should be directed.
    #     The root node is not of type 'Start'.
    #     """
    #
    #     invalid_workflow = None
    #     with open(os.path.join(currpath, '../files/linear-workflow-invalid.jgf')) as wf:
    #         invalid_workflow = json.load(wf)
    #
    #     spec = WorkflowSpec()
    #     self.assertRaises(WorkflowError, spec.load, invalid_workflow)
    #
    #     # Fix the error and try again, fails because Start node not defined
    #     invalid_workflow['graph']['is_directed'] = True
    #     self.assertRaises(WorkflowError, spec.load, invalid_workflow)
    #
    # def test_query_finished_spec(self):
    #     """
    #     Query for global and local metadata on a finished workflow
    #     """
    #
    #     spec = WorkflowSpec()
    #     spec.load(os.path.join(currpath, '../files/linear-workflow-finished.jgf'))
    #
    #     # Query local metadata
    #     task2 = spec.get_task(2)
    #     self.assertEqual(task2['session']['utime'], 1493819368)
    #     self.assertEqual(task2.status, 'completed')
    #     self.assertEqual(task2['session']['utime'] - task2['session']['itime'], 1)
    #
    # def test_build_linear_spec(self):
    #     """
    #     Construct a simple linear workflow specification of 6 nodes
    #     """
    #
    #     spec = WorkflowSpec()
    #
    #     for task in range(5):
    #         nid = spec.add_task(task_name='task{0}'.format(task+1), input_data={'sleep': 0})
    #         if task == 0:
    #             spec.connect_task(1, nid)
    #         else:
    #             spec.connect_task(nid-1, nid)
    #
    #     # Set some metadata
    #     spec.workflow.title = 'Test project'
    #
    # def test_build_branched_spec(self):
    #     """
    #     Construct a branched workflow specification that behaves as a map-reduce
    #     style workflow.
    #     """
    #
    #     spec = WorkflowSpec()
    #
    #     # Add task nodes
    #     for task in range(9):
    #         nid = spec.add_task('task{0}'.format(task+1), input_data={'sleep': 0})
    #     spec.workflow.nodes[9]['task_type'] = 'Collect'
    #
    #     # Connect tasks
    #     connections = ((1, 2), (2, 3), (3, 4), (4, 5), (4, 7), (5, 6), (7, 8), (8, 9), (6, 9), (9, 10))
    #     for pair in connections:
    #         spec.connect_task(*pair)
    #
    #     # Set some metadata
    #     spec.workflow.title = 'Map-reduce project'
    #     maptask = [n for n in spec.workflow.nodes if len(spec.workflow.adjacency[n]) > 1 and
    #                spec.workflow.nodes[n]['task_type'] == 'Task']
    #     redtask = [n for n in spec.workflow.nodes if spec.workflow.nodes[n]['task_type'] == 'Collect']
    #     self.assertListEqual(maptask, [4])
    #     self.assertListEqual(redtask, [9])
