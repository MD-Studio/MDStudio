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

def _GenerateSequenceItem( template_molecule, sequence_index ):

    linear_molecule_key = _GenerateMoleculeKey(template_molecule.key,sequence_index)
    linear_molecule = template_molecule.SafeCopy( molecule_key=linear_molecule_key )
    
    return linear_molecule


def _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map, template_atom_counts ):

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

        print (sequence_item.Debug())

        # add to solutes
        solute_group.AddMolecule( molecule=sequence_item )
        template_atom_counts[sequence_item.key] = sequence_item.atom_count

        # increment our sequence index
        seq_index+=1


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
    template_atom_counts = dict()
    solute_group = topology.GroupByKey("solute")

    _GeneratePlainSequence( blueprint, sequence, solute_group, chain_cap_map, template_atom_counts )
    _PrepareMoleculeMerge( solute_group, chain_cap_map )
    _AssertBondedInMerge( topology, solute_group, chain_cap_map, template_atom_counts )
    _FinalizeLinking( topology, solute_group, chain_cap_map )
    
    return topology
    