# -*- coding: utf-8 -*-

"""
file: module_liecontactframe_test.py

Test the pylie protein-ligand contact analysis
"""

import os
import unittest2

from pylie.model.liecontactframe import *


class TestLIEContactFrame(unittest2.TestCase):
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files'))

    def test_contact_frame(self):

        mol2 = os.path.join(self.filepath, 'contacts.mol2')

        contacts = LIEContactFrame()
        contacts.from_file(mol2, filetype='mol2')

        # Get the ligand and resolve rings in the structure
        lig = contacts[contacts['resname'] == '15']
        rings = find_rings(lig)

        # Get atoms in the neighbourhood of the ligand (binding cavity)
        # Expand to include full amino-acids
        aa = lig.neighbours()
        aa = contacts[contacts['resnum'].isin(set(aa['resnum'].values))]

        contact_frame = lig.contacts(aa)
        contact_frame = eval_hydrophobic_interactions(contact_frame, contacts)
        contact_frame = eval_hbonds(contact_frame, contacts)
        contact_frame = eval_water_bridges(contact_frame, contacts)
        contact_frame = eval_saltbridge(contact_frame, contacts)
        contact_frame = eval_pistacking(contact_frame, contacts, rings=[r[0] for r in rings if r[1] in ('RPA', 'RPN')])
        contact_frame = eval_pication(contact_frame, contacts)
        contact_frame = eval_halogen_bonds(contact_frame, contacts)
        contact_frame = eval_heme_coordination(contact_frame, contacts, rings=[r[0] for r in rings if r[1] in ('RPA', 'RPN')])
