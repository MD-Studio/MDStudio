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
from lie_topology.molecule.reference import AtomReference
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.topology import Topology
from lie_topology.molecule.dihedral import Dihedral
from lie_topology.molecule.angle import Angle
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.bond import Bond



class Bookkeeping(object):

    def __init__(self):

        self.residue_index = 0
        self.atom_index = 0
        self.chain_length = 0
        self.blend_into = False

##
## We generate references so that we can relink in the new molecule
##
def _GenerateRenameEntry( rtype, entry_name ):

    return "%s::%s" % ( rtype, entry_name )

def _GenerateReference( ref_input, rename_dict ):
    reference = None

    if isinstance( ref_input, Atom ):
        reference = ref_input.ToReference()

    elif isinstance( ref_input, AtomReference ):
        reference = deepcopy(ref_input)

    else:
        raise LieTopologyException("MakeTopology", "Unrecognised type of atom reference")  
    
    # test if we need to apply rename schemes
    if reference.atom_key is not None:
        rename_entry = _GenerateRenameEntry("a", reference.atom_key)
        if rename_entry in rename_dict:
            print( "DEBUG; renaming ", reference.atom_key, rename_dict[rename_entry] )
            reference.atom_key = rename_dict[rename_entry]

    if reference.molecule_key is not None:
        rename_entry = _GenerateRenameEntry("m", reference.molecule_key)
        if rename_entry in rename_dict:
            print( "DEBUG; renaming ", reference.molecule_key, rename_dict[rename_entry] )
            reference.molecule_key = rename_dict[rename_entry]
    
    if reference.group_key is not None:
        rename_entry = _GenerateRenameEntry("g", reference.group_key)
        if rename_entry in rename_dict:
            print( "DEBUG; renaming ", reference.group_key, rename_dict[rename_entry] )
            reference.group_key = rename_dict[rename_entry]

    return reference

def _CopyBonds( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.bonds:
        for bond in src_molecule.bonds:

            if len(bond.atom_references) != 2:
                raise LieTopologyException("MakeTopology", "Bonds require 2 atom references")  

            ref_1 = _GenerateReference( bond.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( bond.atom_references[1], rename_dict )

            dest_molecule.AddBond( Bond( atom_references=[ref_1, ref_2], bond_type=bond.bond_type, sybyl=bond.sybyl ) ) 

def _CopyAngles( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.angles:
        for angle in src_molecule.angles:

            if len(angle.atom_references) != 3:
                raise LieTopologyException("MakeTopology", "Angles require 3 atom references")  

            ref_1 = _GenerateReference( angle.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( angle.atom_references[1], rename_dict )
            ref_3 = _GenerateReference( angle.atom_references[2], rename_dict )

            dest_molecule.AddAngle( Angle( atom_references=[ref_1, ref_2,ref_3], angle_type=angle.angle_type ) )  

def _CopyDihedrals( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.dihedrals:
        for dihedral in src_molecule.dihedrals:

            if len(dihedral.atom_references) != 4:
                raise LieTopologyException("MakeTopology", "Dihedrals require 4 atom references")  

            ref_1 = _GenerateReference( dihedral.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( dihedral.atom_references[1], rename_dict )
            ref_3 = _GenerateReference( dihedral.atom_references[2], rename_dict )
            ref_4 = _GenerateReference( dihedral.atom_references[3], rename_dict )

            dest_molecule.AddDihedral( Dihedral( atom_references=[ref_1,ref_2,ref_3,ref_4], dihedral_type=dihedral.dihedral_type ) )

def _CopyAtoms( src_molecule, dest_molecule, start_index, it_from, it_to ):

    # add atoms
    #for key, atom in src_molecule.atoms.items():
    for i in range(it_from, it_to):

        key, atom=src_molecule.atoms.keyValueAt(i)

        # make sure we ignore preceding atoms that might be in blend data
        if atom.preceding is None or not atom.preceding:

            dest_molecule.AddAtom(  key=key, type_name=atom.type_name, element=atom.element,\
                                    identifier=start_index, sybyl=atom.sybyl,\
                                    mass_type=atom.mass_type, vdw_type=atom.vdw_type,\
                                    coulombic_type=atom.coulombic_type, charge_group=atom.charge_group,\
                                    virtual_site=atom.virtual_site, trailing=atom.trailing )
                                    
            start_index+=1
            #print( atom.key )

def _AddBlend( solute_group, molecule, book_keeping ):

    print( "BLEND ", molecule.key )
    linear_molecule_key = "%s_%i" % (molecule.key,book_keeping.residue_index)
    linear_molecule = Molecule( key=linear_molecule_key, type_name=molecule.type_name, identifier=book_keeping.residue_index )

    _CopyAtoms( molecule, linear_molecule, book_keeping.atom_index, 0, molecule.atom_count )
    _CopyBonds( molecule, linear_molecule, {} )
    _CopyAngles( molecule, linear_molecule, {} )
    _CopyDihedrals( molecule, linear_molecule, {} )

    if molecule.trailing_count > 0:
        if book_keeping.chain_length != 0:
            raise LieTopologyException("MakeTopology", "Can only use a blend start at chain length == 0")
        
        # start a new  chain
        book_keeping.blend_into = True
        solute_group.AddMolecule( molecule=linear_molecule )

    elif molecule.preceding_count > 0:
        if book_keeping.chain_length == 0:
            raise LieTopologyException("MakeTopology", "Cannot cap an empty chain")

    else:
        raise LieTopologyException("MakeTopology", "Sequence item %s is not a chain start or cap, while blending was requested" % (molecule.key))
    

def _AddSolute( solute_group, template_molecule, book_keeping ):

    print( "SOLUTE ", template_molecule.key )

    rename_dict=dict()
    it_start = 0
    it_end = template_molecule.atom_count
    
    linear_molecule_key = "%s_%i" % (template_molecule.key,book_keeping.residue_index)
    linear_molecule = Molecule( key=linear_molecule_key, type_name=template_molecule.type_name, identifier=book_keeping.residue_index )
    
    # make sure we update references to the new situation
    molecule_rename_key = _GenerateRenameEntry("m", template_molecule.key)
    rename_dict[molecule_rename_key] = linear_molecule_key

    if book_keeping.blend_into:
        #pop the last residue which is a blend
        last_key, last_linear_molecule = solute_group.molecules.popitem(pop_last=True) 

        #skip set of atoms
        trailing_count = last_linear_molecule.trailing_count
        it_start = trailing_count

        # perform a range check!
        if trailing_count >= template_molecule.atom_count:
            raise LieTopologyException("MakeTopology", "While blending into a chain start, the number of trailing atoms exceeds or equals the blendin residue count")

        # generate rename
        # we want to keep the blend atom names, so perform a rename
        for i in range(0, trailing_count):
            old_atom_key = template_molecule.atoms.keyAt(i)
            new_atom_key = last_linear_molecule.atoms.keyAt(-trailing_count + i)

            if old_atom_key != new_atom_key:
                atom_rename_key = _GenerateRenameEntry("a", old_atom_key)
                rename_dict[atom_rename_key] = new_atom_key

        # we want to keep the NEW molecule name, so perform a backwards rename
        molecule_rename_key = _GenerateRenameEntry("m", last_key)
        rename_dict[molecule_rename_key] = linear_molecule_key

        # copy stored information into the new molecule with rename
        last_linear_atom_count = last_linear_molecule.atom_count
        _CopyAtoms( last_linear_molecule, linear_molecule, book_keeping.atom_index, 0, last_linear_atom_count )
        _CopyBonds( last_linear_molecule, linear_molecule, rename_dict )
        _CopyAngles( last_linear_molecule, linear_molecule, rename_dict )
        _CopyDihedrals( last_linear_molecule, linear_molecule, rename_dict )
        
        #advance atom counter
        book_keeping.atom_index+=last_linear_atom_count
    
    _CopyAtoms( template_molecule, linear_molecule, book_keeping.atom_index, it_start, it_end )
    _CopyBonds( template_molecule, linear_molecule, rename_dict )
    _CopyAngles( template_molecule, linear_molecule, rename_dict )
    _CopyDihedrals( template_molecule, linear_molecule, rename_dict )

    solute_group.AddMolecule( molecule=linear_molecule )

    book_keeping.atom_index+=linear_molecule.atom_count
    book_keeping.chain_length+=1
    book_keeping.residue_index+=1

    # reset flags
    book_keeping.blend_into = False

def _GenerateSequence( forcefield, blueprint, sequence, topology ):
    
    book_keeping = Bookkeeping()
    solute_group = topology.GroupByKey("solute")
    residue_index = 0

    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)
        blend_template=blueprint.FindBlend(seq_item)

        if molecule_template != None:
            _AddSolute( solute_group, molecule_template, book_keeping )
            book_keeping.blend_into = False
            
        elif blend_template != None:

            if blend_template.preceding_count > 0 and\
               blend_template.trailing_count > 0:
               raise LieTopologyException("MakeTopology", "Sequence item %s cannot be both chain start and cap" % (seq_item))

            _AddBlend( solute_group, blend_template, book_keeping )

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item))

        

##  
## Based on gromos++ make_top
##
def MakeSequence( forcefield, blueprint, sequence, solvent_name, disulfides ):

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

    return topology
    