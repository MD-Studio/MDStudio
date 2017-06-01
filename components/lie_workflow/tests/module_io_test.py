# -*- coding: utf-8 -*-

"""
file: module_io_test.py

Unit tests for workflow import and export to JSON file format
"""

import os
import sys
import unittest2
import logging

# Add modules in package to path so we can import them
currpath = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(currpath, '..')))

from   lie_graph.io.io_json_format import read_json, write_json
from   lie_workflow                import Workflow

from   dummy_task_runners          import TaskRunner

class TestWorkflowImportExport(unittest2.TestCase):
    """
    Test workflow specification construction
    """
    
    def test_json_import_finished(self):
        """
        Read a simple finished linear workflow from file
        """
        
        workflow = read_json(os.path.join(currpath, 'files/linear-workflow-finished.json'))
        
        # Construct the workflow specification
        wf = Workflow(workflow=workflow)
        wf.task_runner = TaskRunner()
        
        self.assertTrue(wf.is_completed)
    
    def test_json_import_unfinished(self):
        """
        Read a simple linear workflow from file that is not yet finished
        and restart it until its finished
        """
        
        workflow = read_json(os.path.join(currpath, 'files/linear-workflow-unfinished.json'))
        
        # Construct the workflow specification
        wf = Workflow(workflow=workflow)
        wf.task_runner = TaskRunner()
        
        self.assertFalse(wf.is_completed)
        
        wf.run()
        self.assertTrue(wf.is_completed)
        

class TestWorkflowStatistics(unittest2.TestCase):
    """
    Test workflow statistics
    """
    
    def test_statistics_runtime(self):
        
        workflow = read_json(os.path.join(currpath, 'files/linear-workflow-finished.json'))
        
        # Construct the workflow specification
        wf = Workflow(workflow=workflow)
        
        self.assertEqual(wf.starttime, 1493819365)
        self.assertEqual(wf.finishtime, 1493819372)
        self.assertEqual(wf.runtime, 7)