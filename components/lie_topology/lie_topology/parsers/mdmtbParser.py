#
# @cond ___LICENSE___
#
# Copyright (c) 2017 K.M. Visscher and individual contributors.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# @endcond
#

import sys
import os
import yaml
import numpy as np

from lie_topology.common.exception        import LieTopologyException
from lie_topology.forcefield.forcefield   import *

from lie_topology.common.util               import ordered_load
from lie_topology.common.tokenizer          import Tokenizer
from lie_topology.common.exception          import LieTopologyException
from lie_topology.molecule.blueprint        import Blueprint
from lie_topology.molecule.molecule         import Molecule
from lie_topology.molecule.bond             import Bond
from lie_topology.molecule.angle            import Angle
from lie_topology.molecule.dihedral         import Dihedral
from lie_topology.molecule.vsite            import InPlaneSite
from lie_topology.molecule.reference        import AtomReference, ForwardChainReference, ReverseChainReference, ExplicitConnectionReference
from lie_topology.forcefield.forcefield     import CoulombicType, BondType
from lie_topology.forcefield.reference      import ForceFieldReference

def GenerateBondedReferences( solute, entries, expected_entries ):

    references = None

    if len(entries) != expected_entries:
        raise LieTopologyException("GenerateBondedReferences", "Expected to find %i entries in the atom indices, instead got %i" % ( expected_entries, len(entries) ))

    references = []

    for entry in entries:

        # check entry prefixes
        if len(entry) == 0 or not isinstance(entry, str):
            raise LieTopologyException("GenerateBondedReferences", "Expected to find an entry of type string instead got %s" % ( str(entry) ) )

        # there are a few options that indicate that this atom is an external atom
        # forward chain references
        if entry[0] == '+':
            references.append( ForwardChainReference( atom_key=entry[1:] ) )
        
        # reverse chain references
        elif entry[0] == '-':
            references.append( ReverseChainReference( atom_key=entry[1:] ) )

        # explicitly defined connection (e.g. HIS % HEME)
        elif entry[0] == '^':
            references.append( ExplicitConnectionReference( atom_key=entry[1:] ) )

        else:
            if not entry in solute.atoms:
                raise LieTopologyException("GenerateBondedReferences", "Referencing to an undefined atom %s" % ( entry ) )

            references.append( solute.atoms[ entry ] )

    return references

def ReadAtomSection( atom_section, solute ):

    for atom_key, atom_data in atom_section.items():

        if not "vdw-type" in atom_data or\
           not "mass-type" in atom_data or\
           not "charge" in atom_data or\
           not "charge-type" in atom_data or\
           not "charge-group" in atom_data:
           
           raise LieTopologyException("ReadAtomSection", "Solute atoms require a vdw-type, mass-type, charge, charge-type and charge-group section")

        vdw_group       = atom_data["vdw-type"]
        mass_group      = atom_data["mass-type"]
        charge         = atom_data["charge"]
        charge_type    = atom_data["charge-type"]
        charge_group   = atom_data["charge-group"]
        
        solute.AddAtom( key=atom_key, type_name=atom_key )
        atom = solute.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        atom.mass_type = ForceFieldReference( key=mass_group )
        atom.vdw_type  = ForceFieldReference( key=vdw_group )
        atom.coulombic_type = ForceFieldReference( key=charge_type )
        
        atom.charge = charge
        atom.charge_group = charge_group

def ReadBondSection( bond_section, solute ):

    for bond_data in bond_section:

        if not "indices" in bond_data or\
           not "type" in bond_data:
           
           raise LieTopologyException("ReadBondSection", "Solute bonds require an indices and type entry")
        
        indices = bond_data["indices"]
        bond_type = bond_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 2 )
        bond = Bond( atom_references=atom_references, forcefield_type=bond_type  )   
        solute.AddBond( bond )

def ReadAngleSection( angle_section, solute ):

    for angle_data in angle_section:

        if not "indices" in angle_data or\
           not "type" in angle_data:
           
           raise LieTopologyException("ReadAngleSection", "Solute angles require an indices and type entry")
        
        indices = angle_data["indices"]
        angle_type = angle_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 3 )
        angle = Angle( atom_references=atom_references, forcefield_type=angle_type  )   
        solute.AddAngle( angle )


def ReadSoluteBlueprints( stream, blueprint ):

    for blueprint_key, blueprint_data in stream.items():

        if not "atoms" in blueprint_data or\
           not "bonds" in blueprint_data or\
           not "angles" in blueprint_data or\
           not "impropers" in blueprint_data or\
           not "dihedrals" in blueprint_data:
           
           raise LieTopologyException("ReadSoluteAtoms", "Solute blueprints require an atoms, bonds, angles, impropers and dihedrals section")

        solute = Molecule( key=blueprint_key, type_name=blueprint_key )

        atom_section = blueprint_data["atoms"]
        bond_section = blueprint_data["bonds"]
        angle_section = blueprint_data["angles"]
        improper_section = blueprint_data["impropers"]
        dihedral_section = blueprint_data["dihedrals"]

        ReadAtomSection( atom_section, solute )
        ReadBondSection( bond_section, solute )
        ReadAngleSection( angle_section, solute )

def ParseSolutes( stream, blueprint ):

    if not "solute_blueprints" in stream:
        raise LieTopologyException("ParseSolutes", "MdAA requires a solute_blueprints section")

    solute_blueprints = stream["solute_blueprints"]

    ReadSoluteBlueprints( solute_blueprints, blueprint )

def ParseMDMtb( ifstream ):

    blueprint = Blueprint()

    stream = ordered_load( ifstream )
    ParseSolutes( stream, blueprint )