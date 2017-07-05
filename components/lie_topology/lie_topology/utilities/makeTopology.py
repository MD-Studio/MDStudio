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

def _GenerateMoleculeKey( molecule_name, index ):

    return "%s_%i" % (molecule_name,index)

def _GenerateSequenceItem( template_molecule, sequence_index, group_key ):

    linear_molecule_key = _GenerateMoleculeKey(template_molecule.key,sequence_index)
    linear_molecule = template_molecule.SafeCopy( molecule_key=linear_molecule_key, group_key=group_key )
    
    return linear_molecule



def _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map, template_atom_counts ):

    seq_index=0
    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)
        blend_template=blueprint.FindBlend(seq_item)

        if molecule_template != None:
            sequence_item = _GenerateSequenceItem( molecule_template, seq_index, solute_group.key )
            
        elif blend_template != None:

            if blend_template.preceding_count > 0 and\
               blend_template.trailing_count > 0:
               raise LieTopologyException("MakeTopology", "Sequence item %s cannot be both chain start and cap" % (seq_item))
            
            sequence_item = _GenerateSequenceItem( blend_template, seq_index, solute_group.key )

            if blend_template.trailing_count > 0:

                chain_cap_map[sequence_item.key] = BlendPosition.chain_start
            else:

                chain_cap_map[sequence_item.key] = BlendPosition.chain_end

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item)) 

        # add to solutes
        solute_group.AddMolecule( molecule=sequence_item )
        template_atom_counts[sequence_item.key] = sequence_item.atom_count

        # increment our sequence index
        seq_index+=1

def _RenameBondedReferences( bonded_list, group_key, molecule_key, old_atom_key, new_atom_key):

    for bonded in bonded_list:
        for atom_ref in bonded.atom_references:

            if old_atom_key == atom_ref.atom_key:

                # only if we talk about the same molecule
                if atom_ref.group_key is None or\
                    atom_ref.group_key == group_key:

                    if atom_ref.molecule_key is None or\
                    atom_ref.molecule_key == molecule_key: 
                        atom_ref.atom_key = new_atom_key

def _BondedToTarget( molecule, atom_keys, target_molecule_key ):
    
    response = []
    for bond in molecule.bonds:

        atom_references = bond.atom_references
        ref_1 = atom_references[0].ToReference()
        ref_2 = atom_references[1].ToReference()

        #print ("Testing: ", atom_keys, target_molecule_key, target_group_key, " || ", ref_1.Debug(), ref_2.Debug() )

        # make sure that if both are pointing to same molecule
        # that we do not find known bonds
        # if (  ref_2.molecule_key == target_molecule_key and\
        #     ( ref_2.group_key is None or\
        #       ref_2.group_key == target_group_key ) and\
        #       ref_2.atom_key in atom_keys ) and\
        # not ( molecule.key == target_molecule_key and\
        #       ref_1.atom_key in atom_keys ):
        #     response.append(ref_1)

        if ref_2 in atom_keys and not ref_1 in atom_keys:
            response.append(ref_1)

    return response

def _ReplacePositiveReferences( molecule, next_molecule, atom_references, template_atom_count, offset=0 ):

    for reference in atom_references:
        if reference.IsIndexedReference():
            response = None

            if reference.external_index >= 0:
                #find the relative index of this
                #we use the mapped original atom count at start and end groups
                #might have modified the current atom count
                atom_index = reference.external_index - template_atom_count + offset

                print( "_ReplacePositiveReferences ", len(atom_references), molecule.key, reference.external_index, template_atom_count, " -> ", atom_index)

                if atom_index < next_molecule.atom_count:
                    response = next_molecule.atoms.at(atom_index).ToReference()
            
            if response:
                reference.external_index = None
                reference.group_key = response.group_key
                reference.atom_key = response.atom_key
                reference.molecule_key = response.molecule_key

def _ReplaceNegativeReferences( molecule, prev_molecule, atom_references, nearest_bond_map, allow_multi_bond=False ):

    # find all references to atoms IN molcule
    atom_keys = []
    for reference in atom_references:
        if reference.IsNamedReference():
            # if reference.molecule_key == molecule.key and\
            #   (reference.group_key is None or\
            #    reference.group_key    == molecule.group.key):
                atom_keys.append(reference)
            
    #for reference in atom_references:
    num_references = len(atom_references)

    for i in range(0, num_references):
        fetch_index = num_references - i - 1
        reference = atom_references[fetch_index]
        nearest_bond_list = None

        if fetch_index in nearest_bond_map:
            nearest_bond_list = nearest_bond_map[fetch_index]

        if reference.IsIndexedReference():

            response = None
            if reference.external_index < 0:
                # two options, either the negative index is an "offset" or it indicates that
                # we might want to find the nearst bond. The map indicates if this external index
                # should be tested as bonded, although only for a certain fetch_index (its value)
                if nearest_bond_list is not None and\
                   reference.external_index in nearest_bond_list:

                    # key and mocule.key are the same as we already
                    bond_options = _BondedToTarget(prev_molecule, atom_keys, molecule.key)
                    
                    if not allow_multi_bond and len(bond_options) != 1:
                        print ( "reference.external_index in nearest_bond_map" )
                        for option in bond_options:
                            print ("option: ", option.Debug() )
                        print ( "atom_keys: ", atom_keys )
                        print ( prev_molecule.Debug() )
                        print ( molecule.Debug() )
                        
                        raise LieTopologyException("Molecule::_AssertBonded", "Ambigous bonded assignment" )
                    
                    #just get the last one
                    response=bond_options[-1]

                else: 
                    if abs(reference.external_index) <= prev_molecule.atom_count:
                        atom_index = prev_molecule.atom_count + reference.external_index
                        response = prev_molecule.atoms.at(atom_index).ToReference()


            if response:
                reference.external_index = None
                reference.group_key = response.group_key
                reference.atom_key = response.atom_key
                reference.molecule_key = response.molecule_key

                # print ( "APPENDING ", reference.atom_key )
                # atom_keys.append(reference.atom_key)
                atom_keys.append(reference)



##
## Merge the capping group and the solute
##
def _HandleStartCapping( solute_group, capping_molecule, next_molecule, template_atom_counts ):

    # prepare to Merge a new molecule
    merged_key = "%s->%s" % ( capping_molecule.key, next_molecule.key )

    merged_molecule = capping_molecule.SafeCopy(molecule_key=merged_key, group_key=solute_group.key)
    merged_molecule.group = solute_group
    solute_group.molecules.swap( capping_molecule.key, merged_molecule.key, merged_molecule )

    next_molecule_cpy = next_molecule.SafeCopy(molecule_key=merged_key, group_key=solute_group.key)
    next_molecule_cpy.group = merged_molecule.group

    trailing_count = capping_molecule.trailing_count

    for j in range(0, trailing_count):
        old_atom_key = next_molecule.atoms.keyAt(j)
        new_atom_key = capping_molecule.atoms.keyAt(-trailing_count + j)

        # while the atom is deleted for now (will be replaced later on),  we must make sure that
        # the bonded references are also up to date
        if old_atom_key != new_atom_key:
            _RenameBondedReferences( next_molecule_cpy.bonds,     solute_group.key, next_molecule_cpy.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( next_molecule_cpy.angles,    solute_group.key, next_molecule_cpy.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( next_molecule_cpy.dihedrals, solute_group.key, next_molecule_cpy.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( next_molecule_cpy.impropers, solute_group.key, next_molecule_cpy.key, old_atom_key, new_atom_key)

    # update original bonded
    template_atom_count = template_atom_counts[capping_molecule.key]

    # add a reference that can be used later on
    template_atom_counts[merged_key] = template_atom_counts[next_molecule.key]


    for bond in merged_molecule.bonds:
        _ReplacePositiveReferences( merged_molecule, next_molecule_cpy, bond.atom_references, template_atom_count )

    for angle in merged_molecule.angles:
        _ReplacePositiveReferences( merged_molecule, next_molecule_cpy, angle.atom_references, template_atom_count )
    
    for improper in merged_molecule.impropers:
        _ReplacePositiveReferences( merged_molecule, next_molecule_cpy, improper.atom_references, template_atom_count )

    for dihedral in merged_molecule.dihedrals:
        _ReplacePositiveReferences( merged_molecule, next_molecule_cpy, dihedral.atom_references, template_atom_count )


    # merge the atoms
    for i in range( trailing_count, next_molecule_cpy.atoms.size() ):
        atom = next_molecule_cpy.atoms.at(i)
        merged_molecule.AddAtom( atom=atom )
    
    # merge bonds
    for bond in next_molecule_cpy.bonds:
        if merged_molecule.IndexOfBond( bond ) < 0:
            merged_molecule.AddBond( bond )

    # merge angles
    for angle in next_molecule_cpy.angles:

        # start by resolving references
        # use for both prev (i-1) and i the merged_molecule, as this one already contains the combined bonds
        _ReplaceNegativeReferences( merged_molecule, merged_molecule, angle.atom_references,{}, True )

        if merged_molecule.IndexOfAngle( angle ) < 0:
            merged_molecule.AddAngle( angle )

    # merge improper
    for improper in next_molecule_cpy.impropers:

        # start by resolving references
        # use for both prev (i-1) and i the merged_molecule, as this one already contains the combined bonds
        _ReplaceNegativeReferences( merged_molecule, merged_molecule, improper.atom_references,{}, True )

        if merged_molecule.IndexOfImproper( improper ) < 0:
            merged_molecule.AddImproper( improper )
    
    # treat dihedrals
    for dihedral in next_molecule_cpy.dihedrals:

        # start by resolving references
        # use for both prev (i-1) and i the merged_molecule, as this one already contains the combined bonds
        _ReplaceNegativeReferences( merged_molecule, merged_molecule, dihedral.atom_references,{ 0 : [-2,-3] }, True )
        
        # in this case test the first 3 references 
        found = None
        for ref_dihedral in merged_molecule.dihedrals:
            if ref_dihedral.atom_references[0] == dihedral.atom_references[0] and\
               ref_dihedral.atom_references[1] == dihedral.atom_references[1] and\
               ref_dihedral.atom_references[2] == dihedral.atom_references[2]:

               found = ref_dihedral
                  
        if found:
            # switch reference 4
            found.atom_references[3] = dihedral.atom_references[3]

        else:
            merged_molecule.AddDihedral( dihedral )
    
    return merged_molecule

def _HandleEndCapping( solute_group, capping_molecule, prev_molecule, template_atom_counts ):

    # prepare to Merge a new molecule
    merged_key = "%s->%s" % ( prev_molecule.key, capping_molecule.key )
    
    merged_molecule = prev_molecule.SafeCopy(molecule_key=merged_key, group_key=solute_group.key)
    merged_molecule.group = solute_group
    solute_group.molecules.swap( prev_molecule.key, merged_molecule.key, merged_molecule )

    capping_molecule_cpy = capping_molecule.SafeCopy(molecule_key=merged_key, group_key=solute_group.key)
    capping_molecule_cpy.group = merged_molecule.group
    
    #truncate the preceding atoms
    preceding_count = capping_molecule_cpy.preceding_count
    previous_atom_count = merged_molecule.atom_count

    if preceding_count >= previous_atom_count:
        raise LieTopologyException("MakeTopology", "Preceding count of capping group is >= number of atoms previous molecule")

    remove_list = []
    for i in range(0, preceding_count):
        # does not increment as we directly delete the atoms
        fetch_index = previous_atom_count - preceding_count + i 
        old_atom_key = merged_molecule.atoms.keyAt(fetch_index)
        new_atom_key = capping_molecule_cpy.atoms.keyAt(i)
        
        print( "RENAME ", old_atom_key, " to ", new_atom_key )

        remove_list.append(old_atom_key)

        # while the atom is deleted for now (will be replaced later on),  we must make sure that
        # the bonded references are also up to date
        if old_atom_key != new_atom_key:
            _RenameBondedReferences( merged_molecule.bonds,     solute_group.key, merged_molecule.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( merged_molecule.angles,    solute_group.key, merged_molecule.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( merged_molecule.dihedrals, solute_group.key, merged_molecule.key, old_atom_key, new_atom_key)
            _RenameBondedReferences( merged_molecule.impropers, solute_group.key, merged_molecule.key, old_atom_key, new_atom_key)
    
    #perform the actual removing
    for remove_key in remove_list:
        merged_molecule.atoms.remove(remove_key)

    # update original bonded
    template_atom_count = template_atom_counts[prev_molecule.key]
    template_atom_counts[merged_key] = template_atom_count

    for bond in merged_molecule.bonds:
        _ReplacePositiveReferences( merged_molecule, capping_molecule_cpy, bond.atom_references, template_atom_count, offset=preceding_count )

    for angle in merged_molecule.angles:
        _ReplacePositiveReferences( merged_molecule, capping_molecule_cpy, angle.atom_references, template_atom_count, offset=preceding_count )
    
    for improper in merged_molecule.impropers:
        _ReplacePositiveReferences( merged_molecule, capping_molecule_cpy, improper.atom_references, template_atom_count, offset=preceding_count )

    for dihedral in merged_molecule.dihedrals:
        _ReplacePositiveReferences( merged_molecule, capping_molecule_cpy, dihedral.atom_references, template_atom_count, offset=preceding_count )

    # merge the atoms
    for atom in capping_molecule_cpy.atoms.values():
        if not atom.preceding:
            merged_molecule.AddAtom( atom=atom )
    
    # merge bonds
    for bond in capping_molecule_cpy.bonds:

        # start by resolving references
        _ReplaceNegativeReferences( capping_molecule_cpy, merged_molecule, bond.atom_references,{ 0 : [-1,-2] } )

        print  ( "TTTTT ", bond.Debug())

        bond_index = merged_molecule.IndexOfBond( bond ) 
        if bond_index < 0:
            print  ( "ADDING ", bond.Debug())
            merged_molecule.AddBond( bond )
        else:
            print  ( "REPLACING ", bond.Debug())
            # switch the type
            merged_molecule.bonds[bond_index].forcefield_type = bond.forcefield_type
    
    # merge angles
    for angle in capping_molecule_cpy.angles:

        # start by resolving references
        _ReplaceNegativeReferences( capping_molecule_cpy, merged_molecule, angle.atom_references,{ 0 : [-1,-2] } )

        angle_index = merged_molecule.IndexOfAngle( angle ) 
        if angle_index < 0:
            merged_molecule.AddAngle( angle )
        else:
            # switch the type
            merged_molecule.angles[angle_index].forcefield_type = angle.forcefield_type

    # merge impropers
    for improper in capping_molecule_cpy.impropers:

        # start by resolving references
        _ReplaceNegativeReferences( capping_molecule_cpy, merged_molecule, improper.atom_references,{ 0 : [-1,-2,-3,-4],
                                    1 : [-1,-2,-3,-4], 2 : [-1,-2,-3,-4], 3 : [-1,-2,-3,-4] } )

        improper_index = merged_molecule.IndexOfImproper( improper ) 
        if improper_index < 0:
            merged_molecule.AddImproper( improper )
        else:
            # switch the type
            merged_molecule.impropers[improper_index].forcefield_type = improper.forcefield_type

    # merge dihedrals
    for dihedral in capping_molecule_cpy.dihedrals:

        # start by resolving references
        _ReplaceNegativeReferences( capping_molecule_cpy, merged_molecule, dihedral.atom_references,{ 0 : [-1,-2,-3,-4],
                                    1 : [-1,-2,-3,-4], 2 : [-1,-2,-3,-4], 3 : [-1,-2,-3,-4] } )

        dihedral_index = merged_molecule.IndexOfDihedral( dihedral ) 
        if dihedral_index < 0:
            merged_molecule.AddDihedrals( dihedral )
        else:
            # switch the type
            merged_molecule.dihedrals[dihedral_index].forcefield_type = dihedral.forcefield_type

    return merged_molecule

def _HandleCappingGroups( solute_group, chain_cap_map, template_atom_counts, chain_lengths ):

    remove_list = []
    chain_length = 0

    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i) 

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map:
            chain_cap_map_entry = chain_cap_map[molecule.key]
            
            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:
               chain_molecule = solute_group.molecules.at(i+1)

               #check if there are no connected end groups
               if chain_molecule.key in chain_cap_map:
                   raise LieTopologyException("MakeTopology", "Molecule after start %s should be a normal chain molecule" % ( molecule.key ) )  

               merged_molecule = _HandleStartCapping(solute_group, molecule, chain_molecule, template_atom_counts)
               remove_list.append(chain_molecule.key)

            # this is a chain end
            elif chain_cap_map_entry == BlendPosition.chain_end:
                chain_molecule = solute_group.molecules.at(i-1)

                #check if there are no connected end groups
                if chain_molecule.key in chain_cap_map:
                   raise LieTopologyException("MakeTopology", "Molecule before end %s should be a normal chain molecule" % ( molecule.key ) )  

                merged_molecule = _HandleEndCapping(solute_group, molecule, chain_molecule, template_atom_counts)
                remove_list.append(molecule.key)
    
                # reset chain length
                chain_lengths.append(chain_length)
                chain_length = 0

        else:
            # only take into account non-virtual residues
            chain_length+=1

    #flush
    if chain_length > 0:
        chain_lengths.append(chain_length)

    # remove molecules
    for remove_key in remove_list:
        solute_group.molecules.remove(remove_key)


def _FinalizeLinking( solute_group, chain_lengths, template_atom_counts ):

    residue_index=0

    #process complete chain
    for chain_size in chain_lengths:

        local_index = 0
        local_end = (chain_size-1)

        for i in range(0, chain_size):
            is_start = local_index == 0
            is_end   = local_index == local_end
            fetch_index = residue_index + local_index
            molecule = solute_group.molecules.at(fetch_index)
            template_atom_count = template_atom_counts[molecule.key]

            prev_molecule = None
            next_molecule = None

            if not is_start:
                prev_molecule = solute_group.molecules.at(fetch_index-1)
            
            if not is_end:
                next_molecule = solute_group.molecules.at(fetch_index+1)
            
            ##
            ## TODOODODOD check for duplicates
            ##
            for bond in molecule.bonds:
                if next_molecule: 
                    _ReplacePositiveReferences( molecule, next_molecule, bond.atom_references, template_atom_count, offset=0 )
                
                if prev_molecule:
                    _ReplaceNegativeReferences( molecule, prev_molecule, bond.atom_references, {}, allow_multi_bond=False )
                
            for angle in molecule.angles:
                if next_molecule: 
                    _ReplacePositiveReferences( molecule, next_molecule, angle.atom_references, template_atom_count, offset=0 )
                
                if prev_molecule:
                    _ReplaceNegativeReferences( molecule, prev_molecule, angle.atom_references, {}, allow_multi_bond=False )

            for improper in molecule.impropers:
                if next_molecule: 
                    _ReplacePositiveReferences( molecule, next_molecule, improper.atom_references, template_atom_count, offset=0 )
                
                if prev_molecule:
                    _ReplaceNegativeReferences( molecule, prev_molecule, improper.atom_references, {}, allow_multi_bond=False )

            for dihedral in molecule.dihedrals:
                if next_molecule: 
                    _ReplacePositiveReferences( molecule, next_molecule, dihedral.atom_references, template_atom_count, offset=0 )
                
                if prev_molecule:
                    _ReplaceNegativeReferences( molecule, prev_molecule, dihedral.atom_references, { 0: [-3] }, allow_multi_bond=False )
            
            local_index+=1

        # global increment
        residue_index += chain_size
        print ( "chain_size: ", chain_size )

        


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

    chain_lengths = []
    chain_cap_map = dict()
    template_atom_counts = dict()
    solute_group = topology.GroupByKey("solute")

    _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map, template_atom_counts )
    _HandleCappingGroups( solute_group, chain_cap_map, template_atom_counts, chain_lengths )

    print  ("FINAL_LINKING -----------------------------------------------------------------------")
    _FinalizeLinking( solute_group, chain_lengths, template_atom_counts )

    # _PrepareMoleculeMerge( solute_group, chain_cap_map )
    # _AssertBondedInMerge( topology, solute_group, chain_cap_map, template_atom_counts )
    # _FinalizeLinking( topology, solute_group, chain_cap_map )
    
    return topology
    