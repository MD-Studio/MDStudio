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

from   dummy_task_runners          import task_runner

class TestWorkflowBreakpoints(unittest2.TestCase):
    """
    Test workflow breakpoints
    """
    
    def test_single_breakpoint(self):
        
        workflow = read_json(os.path.join(currpath, 'files/linear-workflow-singlebreakpoint.json'))
        
        # Construct the workflow specification
        wf = Workflow(workflow=workflow)
        wf.task_runner = task_runner()
        wf.run()
        
        self.assertFalse(wf.is_completed)
        self.assertEqual(wf.active_breakpoint, 3)
        
        wf.step_breakpoint(wf.active_breakpoint)
        wf.run()
        
        self.assertTrue(wf.is_completed)
        self.assertEqual(wf.active_breakpoint, None)