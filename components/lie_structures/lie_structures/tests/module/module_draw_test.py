# -*- coding: utf-8 -*-

"""
Unit tests for fingerprint methods
"""

import os
import unittest2

from lie_structures.cheminfo_molhandle import mol_read
from lie_structures import toolkits


class CheminfoMolDrawTests(unittest2.TestCase):
    currpath = os.path.dirname(__file__)

    def test_2d_draw(self):

        for toolkit in toolkits:
            mol = mol_read('c1(cccnc1Nc1cc(ccc1)C(F)(F)F)C(=O)O', mol_format='smi', toolkit=toolkit)
            outfile = os.path.join(self.currpath, '../files/{0}_draw.pdf'.format(toolkit))
            if mol:
                mol.draw(filename=outfile, show=False)