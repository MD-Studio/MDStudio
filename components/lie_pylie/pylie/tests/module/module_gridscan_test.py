# -*- coding: utf-8 -*-

"""
file: module_gridscan_test.py

Test the pylie LIEScanDataFrame methods
"""

import os
import unittest2

from pandas import read_csv

from pylie import LIEScanDataFrame, LIEDataFrame


class TestLIEScanDataFrame(unittest2.TestCase):
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files'))
    tempfiles = []

    def setUp(self):
        """
        Import processed LIE VdW and Coulomb energies for several cases into a LIEDataFrame
        """

        cyp1a2 = os.path.join(self.filepath, 'liedata_CYP1a2.csv')
        self.liedata = LIEDataFrame(read_csv(cyp1a2))
        if 'Unnamed: 0' in self.liedata:
            del self.liedata['Unnamed: 0']

    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the working directory
        """

        for tmpfile in self.tempfiles:
            if os.path.isfile(tmpfile):
                os.remove(tmpfile)

        self.tempfiles = []

    def test_scanframe_plots(self):
        """
        Test creation of custom LIEScanDataFrame plot types
        """

        abscan = LIEScanDataFrame()
        abscan.scan(self.liedata)

        for plot_type in ('simmatrix', 'optimal', 'error', 'density', 'vector'):
            export = os.path.join(self.filepath, 'alphabetascan_{0}.pdf'.format(plot_type))
            fig = abscan.plot(kind=plot_type)
            fig.savefig(export)

            self.tempfiles.append(export)
            self.assertTrue(os.path.isfile(export))

    def
