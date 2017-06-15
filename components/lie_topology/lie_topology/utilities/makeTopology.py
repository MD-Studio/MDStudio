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

import numpy as np

from enum import Enum
from copy import deepcopy

from lie_graph import Graph

from lie_topology.common.exception import LieTopologyException
from lie_topology.forcefield.forcefield import ForceField
from lie_topology.molecule.reference import AtomReference
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.topology import Topology
from lie_topology.molecule.dihedral import Dihedral
from lie_topology.molecule.angle import Angle
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.bond import Bond

class BlendPosition(Enum):
    chain_start = 1
    chain_end = 2

### ---------------------------------------------------------------------------------------------------------------------------
### Attempt 2:
### ---------------------------------------------------------------------------------------------------------------------------

def _GenerateMoleculeKey( molecule_name, index ):

    return "%s_%i" % (molecule_name,index)

def _GenerateSequenceItem( template_molecule, sequence_index ):

    print( "Sequence Item", template_molecule.key )

    linear_molecule_key = _GenerateMoleculeKey(template_molecule.key,sequence_index)
    linear_molecule = template_molecule.SafeCopy( molecule_key=linear_molecule_key )
    
    return linear_molecule


def _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map ):

    seq_index=0
    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)
        blend_template=blueprint.FindBlend(seq_item)

        if molecule_template != None:
            sequence_item = _GenerateSequenceItem( molecule_template, seq_index )
            
        elif blend_template != None:

            if blend_template.preceding_count > 0 and\
               blend_template.trailing_count > 0:
               raise LieTopologyException("MakeTopology", "Sequence item %s cannot be both chain start and cap" % (seq_item))
            
            sequence_item = _GenerateSequenceItem( blend_template, seq_index )

            if blend_template.trailing_count > 0:

                chain_cap_map[sequence_item.key] = BlendPosition.chain_start
            else:

                chain_cap_map[sequence_item.key] = BlendPosition.chain_end

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item)) 

        # add to solutes
        solute_group.AddMolecule( molecule=sequence_item )

        # increment our sequence index
        seq_index+=1

def _RemoveOutOfBoundsBonded( bonded_src, is_start = False, is_end = False ):

    to_remove=[]
    for i in range(0, len(bonded_src) ):
        bonded = bonded_src[i]

        schedule_removal=False
        for atom_ref in bonded.atom_references:
            naked_reference = atom_ref.ToReference()

            if naked_reference.IsIndexedReference():
                if is_start and naked_reference.external_index <= 0 or\
                   is_end   and naked_reference.external_index > 0:
                   schedule_removal = True
                   break # hard override on remove

        if schedule_removal:
            to_remove.append(i)
    
    for i in sorted(to_remove, reverse=True):
        del bonded_src[i]

def _FixIndexReference( molecule, atom_reference, bond_graph ):

    external_index = atom_reference.external_index

    group = molecule.group
    if group is None:
        raise LieTopologyException("Molecule::_FixIndexReferences", "Cannot resolve indexed references when group link is undefined" )

    #find the relative index of this
    this_index = group.molecules.indexOf(molecule.key)

    # if a forward reference
    if external_index > 0:
        atom_index = external_index - molecule.atom_count 
        molecule_index = this_index + 1

        next_molecule = group.molecules.at( molecule_index )
        
        # if that was resolved 
        if next_molecule:
            if atom_index < next_molecule.atom_count:
                response = next_molecule.atoms.at(atom_index).ToReference()

                atom_reference.external_index = None
                atom_reference.group_key = response.group_key
                atom_reference.atom_key = response.atom_key
                atom_reference.molecule_key = response.molecule_key
    
    elif external_index < 0:
        atom_index = external_index - molecule.atom_count 
        molecule_index = this_index - 1
    
        prev_molecule = group.molecules.at( molecule_index )
    else:
        raise LieTopologyException("Molecule::_FixIndexReferences", "Reference indices cannot have value 0" )

def _AssertBonded( molecule, bonded_list ):

    for bonded in bonded_list:
        if not bonded.IsReferenceResolved():
            for reference in bonded.atom_references:
                if reference.IsIndexedReference():

                    group = molecule.group
                    if group is None:
                        raise LieTopologyException("Molecule::_AssertBonded", "Cannot resolve indexed references when group link is undefined" )
                    
                    response = None
                    this_index = group.molecules.indexOf(molecule.key)

                    if reference.external_index > 0:

                        #find the relative index of this
                        atom_index = reference.external_index - molecule.atom_count 
                        molecule_index = this_index + 1
                        next_molecule = group.molecules.at( molecule_index )
                        
                        if next_molecule:
                            if atom_index < next_molecule.atom_count:
                                response = next_molecule.atoms.at(atom_index).ToReference()
                    
                    else:

                        print( this_index, this_index - 1 )
                        molecule_index = this_index - 1
                        prev_molecule = group.molecules.at( molecule_index )

                        if prev_molecule:
                            if abs(reference.external_index) < prev_molecule.atom_count:
                                atom_index = prev_molecule.atom_count + reference.external_index
                                print( molecule.key, atom_index, prev_molecule.atom_count, reference.external_index )
                                response = prev_molecule.atoms.at(atom_index).ToReference()


                    if response:
                        reference.external_index = None
                        reference.group_key = response.group_key
                        reference.atom_key = response.atom_key
                        reference.molecule_key = response.molecule_key

def _AssertBondedInMerge(topology, solute_group, chain_cap_map):

    bond_graph = Graph()

    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i) 

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map:
            chain_cap_map_entry = chain_cap_map[molecule.key]
            chain_molecule = None
            is_start = False
            is_end = False

            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:
               chain_molecule = solute_group.molecules.at(i+1)
               is_start = True
            
            # this is a chain end
            elif chain_cap_map_entry == BlendPosition.chain_end:
                chain_molecule = solute_group.molecules.at(i-1)
                is_end = True
            
            if chain_molecule:
                _RemoveOutOfBoundsBonded( chain_molecule.bonds, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.angles, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.dihedrals, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.impropers, is_start=is_start, is_end=is_end )
        
        # Fix bonded
        _AssertBonded( molecule, molecule.bonds )
        _AssertBonded( molecule, molecule.angles )
        _AssertBonded( molecule, molecule.dihedrals )
        _AssertBonded( molecule, molecule.impropers )

        # Generate bond graph
        molecule.ResolveReferences(topology)

def _PrepareStartMerge( i, chain_size, solute_group, molecule, chain_cap_map ):

    # check error states
    if chain_size != 0:
        raise LieTopologyException("MakeTopology", "Can only use a blend start at chain length == 0")
    
    if (i+1) >= solute_group.molecules.size():
        raise LieTopologyException("MakeTopology", "Chain start cannot be at the end of a sqeuence")
    
    # find the next molecule in the chain
    next_molecule = solute_group.molecules.at(i+1)
    
    if next_molecule.key in chain_cap_map:
        raise LieTopologyException("MakeTopology", "Chain start cannot be followed by another blend molecule")
    
    trailing_count = molecule.trailing_count

    # first step is to rename all atoms in the target to the new
    # atom naming scheme. While these atoms will be deleted anyway
    # this is still required to correct all references to the bondeds
    for j in range(0, trailing_count):

        # as we directly delete the atoms, the index of 0
        # is always the start
        old_atom_key = next_molecule.atoms.keyAt(0)
        new_atom_key = molecule.atoms.keyAt(-trailing_count + j)

        # delete the atom
        next_molecule.atoms.remove(old_atom_key)

def _PrepareEndMerge( i, chain_size, solute_group, molecule, chain_cap_map ):

    if chain_size == 0:
        raise LieTopologyException("MakeTopology", "Cannot cap an empty chain")

    if (i-1) < 0:
        raise LieTopologyException("MakeTopology", "Capping group cannot be the first in sequence")

    prev_molecule = solute_group.molecules.at(i-1)    

    #truncate the preceding atoms
    preceding_count = molecule.preceding_count
    previous_atom_count = prev_molecule.atom_count
    if preceding_count >= previous_atom_count:
        raise LieTopologyException("MakeTopology", "Preceding count of capping group is >= number of atoms previous molecule")

    for i in range(0, preceding_count):
        # does not increment as we directly delete the atoms
        fetch_index = previous_atom_count-preceding_count
        old_atom_key = prev_molecule.atoms.keyAt(fetch_index)
        new_atom_key = molecule.atoms.keyAt(i)

        prev_molecule.atoms.remove(old_atom_key)

        #_AssertBondedInMerge( prev_molecule, old_atom_key, new_atom_key )
    
    # remove all preceding atoms
    remove_list=[]
    for atom_key, atom in molecule.atoms.items():
        if atom.preceding:
            remove_list.append(atom_key)
    
    #perform the actual removing
    for remove_key in remove_list:
        molecule.atoms.remove(remove_key)

    #remove out of bounds bonded
    _RemoveOutOfBoundsBonded( prev_molecule.bonds, is_end=True )
    _RemoveOutOfBoundsBonded( prev_molecule.angles, is_end=True )
    _RemoveOutOfBoundsBonded( prev_molecule.dihedrals, is_end=True )
    _RemoveOutOfBoundsBonded( prev_molecule.impropers, is_end=True )

def _PrepareMoleculeMerge(solute_group, chain_cap_map):
    
    """ Prepares molecules for merging

    Blend groups are not residues by themselfs and therefore have to be merged into
    others. Before we can do this we need to make sure that we remove the blended atoms
    from the target and filter the bonded interactions to reflect this.
    """
    chain_size=0
    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i)

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map:
            chain_cap_map_entry = chain_cap_map[molecule.key]

            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:

                _PrepareStartMerge( i, chain_size, solute_group, molecule, chain_cap_map )
            
            # this is a chain end
            elif chain_cap_map_entry == BlendPosition.chain_end:

                _PrepareEndMerge( i, chain_size, solute_group, molecule, chain_cap_map )

        # Otherwise start a capping operation       
        else: 
            chain_size+=1

##  
## Based on gromos++ make_top
##
def MakeSequence( forcefield, blueprint, sequence, solvent_name, disulfides ):

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
    
    if not isinstance(solvent_name, str):
        raise LieTopologyException("MakeTopology", "solvent_name argument should be of type str")

    if not isinstance(disulfides, list):
        raise LieTopologyException("MakeTopology", "disulfides argument should be of type list")

    for seq_instance in sequence:
        if not isinstance(seq_instance, str):
            raise LieTopologyException("MakeTopology", "sequence values should be of type str")
    
    for dis_instance in disulfides:
        if not isinstance(dis_instance, list) or\
            len(dis_instance) != 2:
                raise LieTopologyException("MakeTopology", "disulfides values should be of type list with length 2")
            
        if not isinstance(dis_instance[0], Molecule) or\
           not isinstance(dis_instance[1], Molecule):
            raise LieTopologyException("MakeTopology", "disulfides inputs should be of type Molecule")

    # the notion of a chain disappears, we just have solute and solvent groups now
    # all functions working with a linked topology expect just these 2 groups
    topology = Topology()
    topology.AddGroup( key="solute" )
    topology.AddGroup( key="solvent" )

    chain_cap_map = dict()
    solute_group = topology.GroupByKey("solute")

    _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map )
    _PrepareMoleculeMerge( solute_group, chain_cap_map )
    _AssertBondedInMerge( topology, solute_group, chain_cap_map )
    
    

    return topology
    