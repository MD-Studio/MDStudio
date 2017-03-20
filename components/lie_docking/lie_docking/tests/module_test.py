# -*- coding: utf-8 -*-

"""
Unit tests for the docking component
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

from   twisted.logger             import Logger
from   lie_docking.plants_docking import PlantsDocking
from   lie_docking.utils          import prepaire_work_dir

logging = Logger()

class PlantsDockingTest(unittest.TestCase):
    
    workdir = None
    ligand_file = os.path.join(__rootpath__, 'ligand.mol2')
    protein_file = os.path.join(__rootpath__, 'protein.mol2')
    exec_path = os.path.join(__rootpath__, '../../../bin/plants_darwin')
    
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
        
        if self.workdir and os.path.exists(self.workdir):
            shutil.rmtree(self.workdir)
    
    def test_plants_faultyworkdir(self):
        """
        Docking is unable to start if the working directory 
        is not available and cannot be created
        """
        
        plants = PlantsDocking(workdir='/Users/_dummy_user/lie_docking-0.1/tests/plants_docking',
                               exec_path=self.exec_path,
                               bindingsite_center=[7.79934,9.49666,3.39229])
        
        self.assertFalse(plants.run(self.protein, self.ligand))
    
    def test_plants_faultyexec(self):
        """
        Docking is unable to start if the PLANTS executable
        is not found
        """
        
        self.workdir = prepaire_work_dir(__rootpath__, create=True)
        plants = PlantsDocking(workdir=self.workdir,
                               exec_path='/Users/_dummy_user/lie_docking-0.1/tests/plants',
                               bindingsite_center=[7.79934,9.49666,3.39229])
        
        self.assertFalse(plants.run(self.protein, self.ligand))
            
    def test_plants_docking(self):
        """
        A working plants docking
        """
        
        self.workdir = prepaire_work_dir(__rootpath__, create=True)
        plants = PlantsDocking(workdir=self.workdir, 
                               exec_path=self.exec_path,
                               bindingsite_center=[7.79934,9.49666,3.39229])
        self.assertTrue(plants.run(self.protein, self.ligand))
        
        outputfiles = glob.glob('{0}/_entry_00001_conf_*.mol2'.format(self.workdir))
        self.assertEqual(len(outputfiles), plants._config['cluster_structures'])
        self.assertEqual(len(outputfiles), len(plants.results()))