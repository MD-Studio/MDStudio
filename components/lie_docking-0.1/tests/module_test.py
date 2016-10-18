# -*- coding: utf-8 -*-

"""
Unit tests for the docking component

TODO: Add wamp_services unittests
"""

import os
import sys
import unittest
import shutil
import time
import glob

# Add modules in package to path so we can import them
__rootpath__ = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(__rootpath__, '..')))

from   twisted.logger import Logger

from   lie_docking.plants_docking import PlantsDocking

logging = Logger()

class PlantsDockingTest(unittest.TestCase):
    
    workdir = os.path.join(__rootpath__, 'plants_docking')
    ligand_file = os.path.join(__rootpath__, 'ligand.mol2')
    protein_file = os.path.join(__rootpath__, 'protein.mol2')
    
    @classmethod
    def setUpClass(cls):
        """
        PlantsDockingTest class setup
      
        Read structure files for docking
        """
        
        with open(cls.protein_file, 'r') as pfile:
            cls.protein = pfile.read()
        
        with open(cls.ligand_file, 'r') as lfile:
            cls.ligand = lfile.read()
    
    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the working directory
        """
        
        if os.path.exists(self.workdir):
            shutil.rmtree(self.workdir)
    
    def test_plants_faultyworkdir(self):
        """
        Docking is unable to start if the working directory 
        is not available and cannot be created
        """
        
        workdir = '/Users/_dummy_user/lie_docking-0.1/tests/plants_docking'
        plants = PlantsDocking(workdir)
        plants['bindingsite_center'] = [7.79934,9.49666,3.39229]
        
        self.assertFalse(plants.run(self.protein, self.ligand))
    
    def test_plants_faultyexec(self):
        """
        Docking is unable to start if the PLANTS executable
        is not found
        """
        
        _exec = '/Users/_dummy_user/lie_docking-0.1/tests/plants'
        plants = PlantsDocking(self.workdir, exec_path=_exec)
        plants['bindingsite_center'] = [7.79934,9.49666,3.39229]
        
        self.assertFalse(plants.run(self.protein, self.ligand))
            
    def test_plants_docking(self):
        """
        A working plants docking
        """
        
        plants = PlantsDocking(self.workdir)
        plants['bindingsite_center'] = [7.79934,9.49666,3.39229]
        self.assertTrue(plants.run(self.protein, self.ligand))
        
        outputfiles = glob.glob('{0}/_entry_00001_conf_*.mol2'.format(self.workdir))
        self.assertEqual(len(outputfiles), plants._config['cluster_structures'])
        self.assertEqual(len(outputfiles), len(plants.results()))
        