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

from lie_topology.common.exception            import LieTopologyException
from lie_topology.forcefield.forcefield       import *

from lie_topology.common.util                 import ordered_load
from lie_topology.common.exception            import LieTopologyException
from lie_topology.molecule.blueprint          import Blueprint
from lie_topology.molecule.molecule           import Molecule
from lie_topology.molecule.atom               import AtomStatus
from lie_topology.molecule.bond               import Bond
from lie_topology.molecule.angle              import Angle
from lie_topology.molecule.dihedral           import Dihedral
from lie_topology.molecule.improper           import Improper
from lie_topology.molecule.vsite              import InPlaneSite
from lie_topology.molecule.reference          import AtomReference, ForwardChainReference, ReverseChainReference,\
                                                     ExplicitConnectionReference, VariantTopologyReference
from lie_topology.utilities.generate_variants import GenerateVariants
from lie_topology.forcefield.forcefield       import CoulombicType, BondType
from lie_topology.forcefield.reference        import ForceFieldReference

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
        
        elif entry[0] == '~':
            references.append( VariantTopologyReference( atom_key=entry[1:] ) )
            
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

        vdw_group      = atom_data["vdw-type"]
        mass_group     = atom_data["mass-type"]
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

        # atoms CAN have a status section
        if "status" in atom_data:

            status_str = atom_data["status"]
            atom.status = AtomStatus.StringToEnum(status_str)

            if atom.status is None:
                raise LieTopologyException("ReadAtomSection", "Unknown atom status %s for atom %s" % (status_str, atom_key))


def ReadReplacingSection( replacing_section, solute ):

    for replacing_data in replacing_section:

        if not "src-key" in replacing_data or\
           not "dst-key" in replacing_data or\
           not "vdw-type" in replacing_data or\
           not "mass-type" in replacing_data or\
           not "charge" in replacing_data or\
           not "charge-type" in replacing_data or\
           not "charge-group" in replacing_data:
           
           raise LieTopologyException("ReadReplacingSection", "Solute atoms require a vdw-type, mass-type, charge, charge-type and charge-group section")

        src_key      = replacing_data["src-key"]
        dst_key      = replacing_data["dst-key"]
        vdw_group    = replacing_data["vdw-type"]
        mass_group   = replacing_data["mass-type"]
        charge       = replacing_data["charge"]
        charge_type  = replacing_data["charge-type"]
        charge_group = replacing_data["charge-group"]

        # set type_name to src_key
        solute.AddAtom( key=dst_key, type_name=src_key, status=AtomStatus.replacing )
        atom = solute.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        atom.mass_type = ForceFieldReference( key=mass_group )
        atom.vdw_type  = ForceFieldReference( key=vdw_group )
        atom.coulombic_type = ForceFieldReference( key=charge_type )
        
        atom.charge = charge
        atom.charge_group = charge_group

# def ReadDeleteSection( delete_section, solute ):

#     for atom_key in delete_section:

#         # signal with new type_name as a delete
#         solute.AddAtom( key=src_key, type_name=None, status=AtomStatus.deleting )

def ReadBondSection( bond_section, solute ):

    for bond_data in bond_section:

        if not "indices" in bond_data or\
           not "type" in bond_data:
           
           raise LieTopologyException("ReadBondSection", "Solute bonds require an indices and type entry")
        
        indices = bond_data["indices"]
        bond_type = bond_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 2 )
        bond = Bond( atom_references=atom_references, forcefield_type=ForceFieldReference( key=bond_type ) )   
        solute.AddBond( bond )

def ReadAngleSection( angle_section, solute ):

    for angle_data in angle_section:

        if not "indices" in angle_data or\
           not "type" in angle_data:
           
           raise LieTopologyException("ReadAngleSection", "Solute angles require an indices and type entry")
        
        indices = angle_data["indices"]
        angle_type = angle_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 3 )
        angle = Angle( atom_references=atom_references, forcefield_type=ForceFieldReference( key=angle_type ) )   
        solute.AddAngle( angle )

def ReadDihedralSection( dihedral_section, solute ):

    for dihedral_data in dihedral_section:

        if not "indices" in dihedral_data or\
           not "type" in dihedral_data:
           
           raise LieTopologyException("ReadDihedralSection", "Solute dihedrals require an indices and type entry")
        
        indices = dihedral_data["indices"]
        dihedral_type = dihedral_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 4 )
        dihedral = Dihedral( atom_references=atom_references, forcefield_type=ForceFieldReference( key=dihedral_type ) )   
        solute.AddDihedral( dihedral )

def ReadImproperSection( improper_section, solute ):

    for improper_data in improper_section:

        if not "indices" in improper_data or\
           not "type" in improper_data:
           
           raise LieTopologyException("ReadDihedralSection", "Solute dihedrals require an indices and type entry")
        
        indices = improper_data["indices"]
        improper_type = improper_data["type"]

        atom_references = GenerateBondedReferences( solute, indices, 4 )
        improper = Improper( atom_references=atom_references, forcefield_type=ForceFieldReference( key=improper_type ) )   
        solute.AddImproper( improper )

def ReadSoluteBlueprints( stream, blueprint ):

    for blueprint_key, blueprint_data in stream.items():

        if not "variants" in blueprint_data or\
           not "atoms" in blueprint_data or\
           not "bonds" in blueprint_data or\
           not "angles" in blueprint_data or\
           not "impropers" in blueprint_data or\
           not "dihedrals" in blueprint_data:
           
           raise LieTopologyException("ReadSoluteBlueprints", "Solute blueprints require an atoms, bonds, angles, impropers and dihedrals section")

        solute = Molecule( key=blueprint_key, type_name=blueprint_key )

        variant_section = blueprint_data["variants"]

        atom_section = blueprint_data["atoms"]
        bond_section = blueprint_data["bonds"]
        angle_section = blueprint_data["angles"]
        improper_section = blueprint_data["impropers"]
        dihedral_section = blueprint_data["dihedrals"]

        if variant_section is not None:
            blueprint.UpdateVariantList( blueprint_key, variant_section )

        if atom_section is not None:
            ReadAtomSection( atom_section, solute )
        
        if bond_section is not None:
            ReadBondSection( bond_section, solute )
        
        if angle_section is not None:
            ReadAngleSection( angle_section, solute )
        
        if dihedral_section is not None: 
            ReadDihedralSection( dihedral_section, solute )

        if improper_section is not None:
            ReadImproperSection( improper_section, solute )
        
        blueprint.AddMolecule( molecule=solute )
        
def ReadVariantBlueprints( stream, blueprint ):

    for blueprint_key, blueprint_data in stream.items():

        if not "add" in blueprint_data or\
           not "replace" in blueprint_data or\
           not "bonds" in blueprint_data or\
           not "angles" in blueprint_data or\
           not "impropers" in blueprint_data or\
           not "dihedrals" in blueprint_data:
           
           raise LieTopologyException("ReadVariantBlueprints", "Variant blueprints require an add, replace, delete, bonds, angles, impropers and dihedrals section")

        solute = Molecule( key=blueprint_key, type_name=blueprint_key )

        add_section      = blueprint_data["add"]
        replace_section  = blueprint_data["replace"]
        # delete_section   = blueprint_data["delete"]
        bond_section     = blueprint_data["bonds"]
        angle_section    = blueprint_data["angles"]
        improper_section = blueprint_data["impropers"]
        dihedral_section = blueprint_data["dihedrals"]

        if add_section is not None:
            ReadAtomSection( add_section, solute )
        
        if replace_section is not None:
            ReadReplacingSection( replace_section, solute )

        # if delete_section is not None:
        #     ReadDeleteSection( replace_section, solute )

        if bond_section is not None:
            ReadBondSection( bond_section, solute )
        
        if angle_section is not None:
            ReadAngleSection( angle_section, solute )

        if dihedral_section is not None:
            ReadDihedralSection( dihedral_section, solute )

        if improper_section is not None:
            ReadImproperSection( improper_section, solute )

        blueprint.AddVariantTemplate( molecule=solute )


def ParseSolutes( stream, blueprint ):

    if not "solute_blueprints" in stream:
        raise LieTopologyException("ParseSolutes", "MdAA requires a solute_blueprints section")

    solute_blueprints = stream["solute_blueprints"]

    ReadSoluteBlueprints( solute_blueprints, blueprint )

def ParseVariants( stream, blueprint ):

    if not "variant_blueprints" in stream:
        raise LieTopologyException("ParseVariants", "MdAA requires a variant_blueprints section")

    variant_blueprints = stream["variant_blueprints"]

    ReadVariantBlueprints( variant_blueprints, blueprint ) 

def ParseMDMtb( ifstream ):

    blueprint = Blueprint()

    stream = ordered_load( ifstream )
    ParseSolutes( stream, blueprint )
    ParseVariants( stream, blueprint )
    GenerateVariants( blueprint )

    return blueprint