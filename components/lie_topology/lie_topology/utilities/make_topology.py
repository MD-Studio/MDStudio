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
from lie_topology.molecule.topology         import Topology
from lie_topology.molecule.atom             import AtomStatus
from lie_topology.molecule.bond             import Bond
from lie_topology.molecule.angle            import Angle
from lie_topology.molecule.dihedral         import Dihedral
from lie_topology.molecule.vsite            import InPlaneSite
from lie_topology.molecule.reference        import AtomReference, ForwardChainReference, ReverseChainReference,\
                                                   ExplicitConnectionReference, VariantTopologyReference
from lie_topology.forcefield.forcefield     import CoulombicType, BondType
from lie_topology.forcefield.reference      import ForceFieldReference

def _GenerateMoleculeKey( molecule_name, index ):

    return "%s_%i" % (molecule_name,index)

def _GenerateSequenceItem( template_molecule, sequence_index, group_key ):

    linear_molecule_key = _GenerateMoleculeKey( template_molecule.key, sequence_index)
    linear_molecule     = template_molecule.SafeCopy( molecule_key=linear_molecule_key, group_key=group_key )
    
    return linear_molecule

def _GeneratePlainSequence( blueprint, sequence, solute_group ):

    seq_index=0
    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)

        if molecule_template != None:
            sequence_item = _GenerateSequenceItem( molecule_template, seq_index, solute_group.key )
            
            # add to solutes
            solute_group.AddMolecule( molecule=sequence_item )

            # increment our sequence index
            seq_index+=1

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item)) 


def _ResolveChainReferences( atom_references, molecule, prev_molecule, next_molecule ):

    new_references = []

    for atom_ref in atom_references:

        if isinstance(atom_ref, AtomReference):
            new_references.append(atom_ref)

        elif isinstance(atom_ref, VariantTopologyReference):
            raise LieTopologyException("_ResolveChainReferences", "VariantTopologyReferences have to be resolved before final linking, this most likely means the variant blueprint is corrupt" ) 

        elif isinstance(atom_ref, ForwardChainReference):

            if next_molecule is None:
                raise LieTopologyException("_ResolveChainReferences", "ForwardChainReference is out of bounds on %s" % ( molecule.key ) ) 

            atom_key = atom_ref.atom_key
            
            if not atom_key in next_molecule.atoms:
                raise LieTopologyException("_ResolveChainReferences", "Atom %s does not exist in molecule n+1 %s" % (atom_key, next_molecule.key) ) 
            
            new_references.append(next_molecule.atoms[atom_key].ToReference())

        elif isinstance(atom_ref, ReverseChainReference):

            if prev_molecule is None:
                raise LieTopologyException("_ResolveChainReferences", "ReverseChainReference is out of bounds on %s" % ( molecule.key ) ) 

            atom_key = atom_ref.atom_key

            if not atom_key in prev_molecule.atoms:
                raise LieTopologyException("_ResolveChainReferences", "Atom %s does not exist in molecule n+1 %s" % (atom_key, prev_molecule.key) ) 

            new_references.append(prev_molecule.atoms[atom_key].ToReference())

        elif isinstance(atom_ref, ExplicitConnectionReference):
           raise LieTopologyException("_ResolveChainReferences", "ExplicitConnectionReferences have to be resolved before final linking" ) 
        
        else:
            raise LieTopologyException("_ResolveChainReferences", "Final linking hit an unsupported reference type" ) 

    return new_references

def _ResolveExplicitReferences( atom_references, to_molecule ):

    new_references = []

    for atom_ref in atom_references:
        
        if isinstance(atom_ref, ExplicitConnectionReference):
            
            atom_key = atom_ref.atom_key

            print(atom_key)

            if not atom_key in to_molecule.atoms:
                raise LieTopologyException("_ResolveExplicitReferences", "Atom %s does not exist in linked molecule %s" % (atom_key, to_molecule.key) ) 
            
            new_references.append(to_molecule.atoms[atom_key].ToReference())

        else:
            new_references.append(atom_ref)

    return new_references

def _ExplicitLinking( solute_group, explicit_links ):

    for ( index_1, index_2 ) in explicit_links:

        if index_1 < 0 or index_1 >= len(solute_group.molecules):
            raise LieTopologyException("_ExplicitLinking", "Molecule index %i is out of range" % (index_1) ) 
        
        if index_2 < 0 or index_2 >= len(solute_group.molecules):
            raise LieTopologyException("_ExplicitLinking", "Molecule index %i is out of range" % (index_2) ) 
        
        molecule_1 = solute_group.molecules.at(index_1)
        molecule_2 = solute_group.molecules.at(index_2)
        
        # molecule_1 -> molecule_2
        for bond in molecule_1.bonds:
            bond.atom_references = _ResolveExplicitReferences( bond.atom_references, molecule_2 )
        
        for angle in molecule_1.angles:
            angle.atom_references = _ResolveExplicitReferences( angle.atom_references, molecule_2 )

        for dihedral in molecule_1.dihedrals:
            dihedral.atom_references = _ResolveExplicitReferences( dihedral.atom_references, molecule_2 )

        for improper in molecule_1.impropers:
            improper.atom_references = _ResolveExplicitReferences( improper.atom_references, molecule_2 )
        
        # molecule_2 -> molecule_1
        for bond in molecule_2.bonds:
            bond.atom_references = _ResolveExplicitReferences( bond.atom_references, molecule_1 )
        
        for angle in molecule_2.angles:
            angle.atom_references = _ResolveExplicitReferences( angle.atom_references, molecule_1 )

        for dihedral in molecule_2.dihedrals:
            dihedral.atom_references = _ResolveExplicitReferences( dihedral.atom_references, molecule_1 )

        for improper in molecule_2.impropers:
            improper.atom_references = _ResolveExplicitReferences( improper.atom_references, molecule_1 )


def _FinalizeLinking( solute_group ):

    num_molecules = solute_group.molecules.size()

    for molecule_index in range( 0, num_molecules ):

        molecule = solute_group.molecules.at( molecule_index )
        prev_molecule = None
        next_molecule = None

        if ( molecule_index - 1) >= 0:
            prev_molecule = solute_group.molecules.at( molecule_index - 1 )
        
        if ( molecule_index + 1) < num_molecules:
            next_molecule = solute_group.molecules.at( molecule_index + 1 )

        for bond in molecule.bonds:
            bond.atom_references = _ResolveChainReferences( bond.atom_references, molecule, prev_molecule, next_molecule )
        
        for angle in molecule.angles:
            angle.atom_references = _ResolveChainReferences( angle.atom_references, molecule, prev_molecule, next_molecule )

        for dihedral in molecule.dihedrals:
            dihedral.atom_references = _ResolveChainReferences( dihedral.atom_references, molecule, prev_molecule, next_molecule )

        for improper in molecule.impropers:
            improper.atom_references = _ResolveChainReferences( improper.atom_references, molecule, prev_molecule, next_molecule )

def MakeSequence( forcefield, blueprint, sequence, explicit_links ):

    """ Generate a sequence from small blueprint molecules

    This function is used to turn a series of small molecules into a topology.
    The sequence may included a chain topology with starting and capping blend groups
    """

    ## Analyze input types and check them
    if not isinstance(forcefield, ForceField):
        raise LieTopologyException("MakeTopology", "forcefield argument should be of type ForceField")  
    
    if not isinstance(blueprint, Blueprint):
        raise LieTopologyException("MakeTopology", "blueprint argument should be of type Blueprint")
    
    if not isinstance(sequence, list):
        raise LieTopologyException("MakeTopology", "sequence argument should be of type list")
    
    if not isinstance(explicit_links, list):
        raise LieTopologyException("MakeTopology", "disulfides argument should be of type list")

    for seq_instance in sequence:
        if not isinstance(seq_instance, str):
            raise LieTopologyException("MakeTopology", "sequence values should be of type str")
    
    for dis_instance in explicit_links:
        if not isinstance(dis_instance, list) or\
            len(dis_instance) != 2:
                raise LieTopologyException("MakeTopology", "disulfides values should be of type list with length 2")
            
        if not isinstance(dis_instance[0], int) or\
           not isinstance(dis_instance[1], int):
            raise LieTopologyException("MakeTopology", "disulfides inputs should be of type Molecule")

    # the notion of a chain disappears, we just have solute and solvent groups now
    # all functions working with a linked topology expect just these 2 groups
    topology = Topology()
    topology.AddGroup( key="solute" )
    topology.AddGroup( key="solvent" )

    solute_group = topology.GroupByKey("solute")
    _GeneratePlainSequence( blueprint, sequence, solute_group )
    _ExplicitLinking( solute_group, explicit_links )
    _FinalizeLinking( solute_group )

    return topology