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

from copy import deepcopy

from lie_topology.common.exception import LieTopologyException
from lie_topology.forcefield.forcefield import ForceField
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.topology import Topology
from lie_topology.molecule.reference import AtomReference
from lie_topology.molecule.atom import Atom

class Bookkeeping(object):

    def __init__(self):

        self.residue_index = 0
        self.atom_index = 0

def _GenerateReference( ref_input ):
    reference = None

    if isinstance( ref_input, Atom ):
        reference = ref_input.ToReference()

    elif isinstance( ref_input, AtomReference ):
        reference = deepcopy(ref_input)

    else:
        raise LieTopologyException("MakeTopology", "Unrecognised type of atom reference")  
    
    return reference

def _AddSolute( solute_group, molecule, book_keeping ):

    linear_molecule = Molecule( key=molecule.key, type_name=molecule.type_name, identifier=book_keeping.residue_index )

    # add atoms
    for key, atom in molecule.atoms.items():
        linear_molecule.AddAtom(key=key, type_name=atom.type_name, element=atom.element,\
                                identifier=book_keeping.atom_index, sybyl=atom.sybyl,\
                                mass_type=atom.mass_type, vdw_type=atom.vdw_type,\
                                coulombic_type=atom.coulombic_type, charge_group=atom.charge_group,\
                                virtual_site=atom.virtual_site, preceding=atom.preceding, trailing=atom.trailing )
 
        book_keeping.atom_index+=1
        print( atom.key )

    for bond in molecule.bonds:

        if len(bond.atom_references) != 2:
            raise LieTopologyException("MakeTopology", "Bonds require 2 atom references")  

        ref_1 = _GenerateReference( bond.atom_references[0] )
        ref_2 = _GenerateReference( bond.atom_references[1] )

        linear_molecule.AddBond( atom_references=[ref_1, ref_2], bond_type=bond.bond_type, sybyl=bond.sybyl)
        

def _GenerateSequence( forcefield, blueprint, sequence, topology ):
    
    book_keeping = Bookkeeping()
    solute_group = topology.GroupByKey("solute")
    residue_index = 0

    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)
        blend_template=blueprint.FindBlend(seq_item)

        if molecule_template != None:
            _AddSolute( solute_group, molecule_template, book_keeping )

        elif blend_template != None:
            _AddSolute( solute_group, blend_template, book_keeping )

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item))

        book_keeping.residue_index+=1
##  
## Based on gromos++ make_top
##
def MakeTopology( forcefield, blueprint, sequence, solvent_name, disulfides ):

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

    topology = Topology()
    topology.AddGroup( key="solute" )
    topology.AddGroup( key="solvent" )

    _GenerateSequence( forcefield, blueprint, sequence, topology )
    