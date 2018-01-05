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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

from lie_topology.common.exception        import LieTopologyException
from lie_topology.forcefield.forcefield   import *

from lie_topology.common.util               import ordered_load
from lie_topology.common.exception          import LieTopologyException
from lie_topology.molecule.blueprint        import Blueprint
from lie_topology.molecule.molecule         import Molecule
from lie_topology.molecule.atom             import AtomStatus
from lie_topology.molecule.bond             import Bond
from lie_topology.molecule.angle            import Angle
from lie_topology.molecule.dihedral         import Dihedral
from lie_topology.molecule.vsite            import InPlaneSite
from lie_topology.molecule.reference        import AtomReference, ForwardChainReference, ReverseChainReference,\
                                                   ExplicitConnectionReference, VariantTopologyReference
from lie_topology.forcefield.forcefield     import CoulombicType, BondType
from lie_topology.forcefield.reference      import ForceFieldReference

def MergeVariantAtoms( variant_template, molecule, variant_molecule, replace_set ):

    defered_atoms = []

    for atom_key, atom in variant_template.atoms.items():
        atom_cpy = atom.SafeCopy()

        # Two options: add, replace
        # is replace?
        if atom.status is AtomStatus.replacing:
            
            if not atom.type_name in molecule.atoms:
                raise LieTopologyException("MergeVariantAtoms", "Variant %s replace atom %s is not present in molecule %s" % ( variant_template.key, atom.type_name, molecule.key ) )
        
            replace_set[atom.type_name] = atom_cpy

        # is add?
        elif atom.status is AtomStatus.preceding or\
             atom.status is AtomStatus.default:

             variant_molecule.AddAtom( atom=atom_cpy )

        elif atom.status is AtomStatus.trailing:

            defered_atoms.append(atom_cpy)

        else:
            raise LieTopologyException("MergeVariantAtoms", "No known resolve method for variant template atom %s with status %i" % ( atom_key, atom.status ) )
    
    # add original molecule atoms
    for atom_key, atom in molecule.atoms.items():

        if atom_key in replace_set:

            atom_cpy = replace_set[atom_key]
            atom_cpy.type_name = atom_cpy.key
            variant_molecule.AddAtom( atom=atom_cpy )
        
        else:
            atom_cpy = atom.SafeCopy()
            variant_molecule.AddAtom( atom=atom_cpy )
        
    # add the deferred atoms
    for defered_atom in defered_atoms:
        variant_molecule.AddAtom( atom=defered_atom ) 


def CleanBondedAtomReferences( variant_name, atom_references, replace_set ):

    new_references = []

    for atom_ref in atom_references:

        if isinstance(atom_ref, VariantTopologyReference):
            atom_ref = AtomReference( atom_key=atom_ref.atom_key )

        if atom_ref.atom_key in replace_set:
            atom_ref.atom_key = replace_set[atom_ref.atom_key].key

        atom_ref.molecule_key = variant_name

        new_references.append(atom_ref)

    return new_references

def MergeVariantBonds( variant_name, variant_template, molecule, variant_molecule, replace_set ):

    # original molecule bonds
    for bond in molecule.bonds:

        bond_cpy = bond.SafeCopy()
        bond_cpy.atom_references = CleanBondedAtomReferences( variant_name, bond_cpy.atom_references, replace_set )
        
        variant_molecule.AddBond(bond_cpy)

    for bond in variant_template.bonds:

        bond_cpy = bond.SafeCopy()
        bond_cpy.atom_references = CleanBondedAtomReferences( variant_name, bond_cpy.atom_references, replace_set )
        bond_index = variant_molecule.IndexOfBond(bond_cpy)

        if bond_index >= 0:

            #now if the force_field type is None in the change we know this is deleted
            if bond_cpy.forcefield_type is None:
                variant_molecule.DeleteBondByIndex(bond_index)

            else:
                # we know that the atom_indices are the same! now switch the FF type
                variant_molecule.bonds[bond_index].forcefield_type = bond_cpy.forcefield_type
        
        else:

            if bond_cpy.forcefield_type is not None: 
                variant_molecule.AddBond(bond_cpy)

def MergeVariantAngles( variant_name, variant_template, molecule, variant_molecule, replace_set ):

    # original molecule angles
    for angle in molecule.angles:

        angle_cpy = angle.SafeCopy()
        angle_cpy.atom_references = CleanBondedAtomReferences( variant_name, angle_cpy.atom_references, replace_set )
        
        variant_molecule.AddAngle(angle_cpy)

    for angle in variant_template.angles:

        angle_cpy = angle.SafeCopy()
        angle_cpy.atom_references = CleanBondedAtomReferences( variant_name, angle_cpy.atom_references, replace_set )
        angle_index = variant_molecule.IndexOfAngle(angle_cpy)
        
        if angle_index >= 0:

            #now if the force_field type is None in the change we know this is deleted
            if angle_cpy.forcefield_type is None:
                variant_molecule.DeleteAngleByIndex(angle_index)
            
            else: 
                # we know that the atom_indices are the same! now switch the FF type
                variant_molecule.angles[angle_index].forcefield_type = angle_cpy.forcefield_type
        
        else:
            variant_molecule.AddAngle(angle_cpy)

def MergeVariantImpropers( variant_name, variant_template, molecule, variant_molecule, replace_set ):

    # original molecule angles
    for improper in molecule.impropers:

        improper_cpy = improper.SafeCopy()
        improper_cpy.atom_references = CleanBondedAtomReferences( variant_name, improper_cpy.atom_references, replace_set )
        
        variant_molecule.AddImproper(improper_cpy)

    for improper in variant_template.impropers:

        improper_cpy = improper.SafeCopy()
        improper_cpy.atom_references = CleanBondedAtomReferences( variant_name, improper_cpy.atom_references, replace_set )
        improper_index = variant_molecule.IndexOfImproper(improper_cpy)
        
        if improper_index >= 0:

            #now if the force_field type is None in the change we know this is deleted
            if improper_cpy.forcefield_type is None:
                variant_molecule.DeleteImproperByIndex(improper_index)
            
            else:
                # we know that the atom_indices are the same! now switch the FF type
                variant_molecule.impropers[improper_index].forcefield_type = improper_cpy.forcefield_type
        
        else:
            variant_molecule.AddImproper(improper_cpy)

def MergeVariantDihedrals( variant_name, variant_template, molecule, variant_molecule, replace_set ):

    # original molecule angles
    for dihedral in molecule.dihedrals:

        dihedral_cpy = dihedral.SafeCopy()
        dihedral_cpy.atom_references = CleanBondedAtomReferences( variant_name, dihedral_cpy.atom_references, replace_set )
        
        variant_molecule.AddDihedral(dihedral_cpy)

    for dihedral in variant_template.dihedrals:
        
        dihedral_cpy = dihedral.SafeCopy()
        dihedral_cpy.atom_references = CleanBondedAtomReferences( variant_name, dihedral_cpy.atom_references, replace_set )
        
        if dihedral_cpy.forcefield_type is None:

            #loop as multiple dihedrals are allowed
            index=variant_molecule.IndexOfDihedral(dihedral_cpy)
            while index >= 0:

                variant_molecule.DeleteDihedralByIndex(index)
                index=variant_molecule.IndexOfDihedral(dihedral_cpy)
        
        else:
            variant_molecule.AddDihedral(dihedral_cpy)


# Maybe this should be moved?
def GenerateVariants( blueprint ):

    for molecule_key, molecule in blueprint.molecules.items():

        variants = blueprint.MoleculeVariants(molecule_key)
        
        for variant_name, variant_key in variants.items():

            variant_template = blueprint.FindVariant(variant_key)

            # use as key the new variant name and as type_name the original molecule
            variant_molecule = Molecule( key=variant_name, type_name=molecule_key )

            if variant_template is None:
                raise LieTopologyException("GenerateVariants", "The topology requested generation of a variant %s for molecule %s, though no blueprint is available for this variant" % ( variant_key, molecule_key ) )
            
            replace_set = {}

            MergeVariantAtoms( variant_template, molecule, variant_molecule, replace_set )
            MergeVariantBonds( variant_name, variant_template, molecule, variant_molecule, replace_set )
            MergeVariantAngles( variant_name, variant_template, molecule, variant_molecule, replace_set )
            MergeVariantImpropers( variant_name, variant_template, molecule, variant_molecule, replace_set )
            MergeVariantDihedrals( variant_name, variant_template, molecule, variant_molecule, replace_set )

            blueprint.AddMolecule( molecule=variant_molecule )