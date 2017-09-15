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

from lie_topology.utilities.neighbour_search import FindExplicitPairs, GenerateBondedGraph

from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.atom import Atom
from lie_topology.forcefield.reference import ForceFieldReference
from lie_topology.forcefield.forcefield import CoulombicType, VdwType, MassType, BondType, AngleType, ImproperType, DihedralType

class GromosBonded(object):

    def __init__(self, gromos_indices, type_index ):

        self.gromos_indices = gromos_indices
        self.type_index = type_index

def _WriteSoluteBonds( solute_group, forcefield, mass_of_hydrogen ):

    gromos_bonds = []

    print("BOND")
    for molecule_key, molecule in solute_group.molecules.items():
        for bond in molecule.bonds:
            
            # all of the force field types could be references
            if not isinstance(bond.forcefield_type, BondType):
                raise LieTopologyException("WriteGromosTopology", "Bond types should be pre-resolved" ) 
            
            # +1 as gromos starts from 1
            bond_type_index = forcefield.bondtypes.indexOf(bond.forcefield_type.key) + 1 

            # negative numbers indicate not found
            if bond_type_index < 0:
                raise LieTopologyException("WriteGromosTopology", "Could not find bond_type %s for atom %s->%s"\
                                           % (bond.forcefield_type.key, molecule.key, atom.key ) ) 
            
            atom_references = bond.atom_references

            if atom_references is None or len(atom_references) != 2:
                raise LieTopologyException("WriteGromosTopology", "Bonds require an atom indices array of size 2" ) 
            
            if not isinstance(atom_references[0], Atom) or\
               not isinstance(atom_references[1], Atom):
                raise LieTopologyException("WriteGromosTopology", "The atom indices for bonds should have been resolve to Atom links" )
            
            # gromos indices start with 1
            atom_index_1 = atom_references[0].internal_index + 1
            atom_index_2 = atom_references[1].internal_index + 1

            gromos_bonds.append( GromosBonded( [atom_index_1, atom_index_2], bond_type_index ) )

            basic_output_str ="%7i%7i%5i" % ( atom_index_1, atom_index_2, bond_type_index )
            print (basic_output_str)
    print("END")

def _WriteSoluteAngles( solute_group, forcefield, mass_of_hydrogen ):

    gromos_angles = []

    print("ANGLE")
    for molecule_key, molecule in solute_group.molecules.items():
        for angle in molecule.angles:
            
            # all of the force field types could be references
            if not isinstance(angle.forcefield_type, AngleType):
                raise LieTopologyException("WriteGromosTopology", "Angle types should be pre-resolved" ) 
            
            angle_type_index = forcefield.angletypes.indexOf(angle.forcefield_type.key) + 1 # +1 as gromos starts from 1

            # negative numbers indicate not found
            if angle_type_index < 0:
                raise LieTopologyException("WriteGromosTopology", "Could not find angle_type %s for atom %s->%s"\
                                           % (angle.forcefield_type.key, molecule.key, atom.key ) ) 
            
            atom_references = angle.atom_references

            if atom_references is None or len(atom_references) != 3:
                raise LieTopologyException("WriteGromosTopology", "Angles require an atom indices array of size 3" ) 
            
            if not isinstance(atom_references[0], Atom) or\
               not isinstance(atom_references[1], Atom) or\
               not isinstance(atom_references[2], Atom):
                raise LieTopologyException("WriteGromosTopology", "The atom indices for angles should have been resolve to Atom links" )
            
            # gromos indices start with 1
            atom_index_1 = atom_references[0].internal_index + 1
            atom_index_2 = atom_references[1].internal_index + 1
            atom_index_3 = atom_references[2].internal_index + 1

            gromos_angles.append( GromosBonded( [atom_index_1, atom_index_2, atom_index_3], angle_type_index ) )

            basic_output_str ="%7i%7i%7i%5i" % ( atom_index_1, atom_index_2, atom_index_3, angle_type_index )
            print (basic_output_str)
    print("END")

def _WriteSoluteImpropers( solute_group, forcefield, mass_of_hydrogen ):

    gromos_impropers = []

    print("IMPROPER")
    for molecule_key, molecule in solute_group.molecules.items():
        for improper in molecule.impropers:
            
            # all of the force field types could be references
            if not isinstance(improper.forcefield_type, ImproperType):
                raise LieTopologyException("WriteGromosTopology", "improper types should be pre-resolved" ) 
            
            improper_type_index = forcefield.impropertypes.indexOf(improper.forcefield_type.key) + 1 # +1 as gromos starts from 1

            # negative numbers indicate not found
            if improper_type_index < 0:
                raise LieTopologyException("WriteGromosTopology", "Could not find improper_type %s for atom %s->%s"\
                                           % (improper.forcefield_type.key, molecule.key, atom.key ) ) 
            
            atom_references = improper.atom_references

            if atom_references is None or len(atom_references) != 4:
                raise LieTopologyException("WriteGromosTopology", "impropers require an atom indices array of size 4" ) 
            
            if not isinstance(atom_references[0], Atom) or\
               not isinstance(atom_references[1], Atom) or\
               not isinstance(atom_references[2], Atom) or\
               not isinstance(atom_references[3], Atom):
                raise LieTopologyException("WriteGromosTopology", "The atom indices for impropers should have been resolve to Atom links" )

            # gromos indices start with 1
            atom_index_1 = atom_references[0].internal_index + 1
            atom_index_2 = atom_references[1].internal_index + 1
            atom_index_3 = atom_references[2].internal_index + 1
            atom_index_4 = atom_references[3].internal_index + 1

            gromos_impropers.append( GromosBonded( [atom_index_1, atom_index_2, atom_index_3, atom_index_4], improper_type_index ) )

            basic_output_str ="%7i%7i%7i%7i%5i" % ( atom_index_1, atom_index_2, atom_index_3, atom_index_4, improper_type_index )            
            print (basic_output_str)
    print("END")

def _WriteSoluteDihedrals( solute_group, forcefield, mass_of_hydrogen ):

    gromos_dihedrals = []

    print("DIHEDRAL")
    for molecule_key, molecule in solute_group.molecules.items():
        for dihedral in molecule.dihedrals:
            
            # all of the force field types could be references
            if not isinstance(dihedral.forcefield_type, DihedralType):
                raise LieTopologyException("WriteGromosTopology", "dihedral types should be pre-resolved" ) 
            
            dihedral_type_index = forcefield.dihedraltypes.indexOf(dihedral.forcefield_type.key) + 1 # +1 as gromos starts from 1

            # negative numbers indicate not found
            if dihedral_type_index < 0:
                raise LieTopologyException("WriteGromosTopology", "Could not find dihedral_type %s for atom %s->%s"\
                                           % (dihedral.forcefield_type.key, molecule.key, atom.key ) ) 
            
            atom_references = dihedral.atom_references

            if atom_references is None or len(atom_references) != 4:
                raise LieTopologyException("WriteGromosTopology", "dihedrals require an atom indices array of size 4" ) 
            
            if not isinstance(atom_references[0], Atom) or\
               not isinstance(atom_references[1], Atom) or\
               not isinstance(atom_references[2], Atom) or\
               not isinstance(atom_references[3], Atom):
                raise LieTopologyException("WriteGromosTopology", "The atom indices for dihedrals should have been resolve to Atom links" )
            
            # gromos indices start with 1
            atom_index_1 = atom_references[0].internal_index + 1
            atom_index_2 = atom_references[1].internal_index + 1
            atom_index_3 = atom_references[2].internal_index + 1
            atom_index_4 = atom_references[3].internal_index + 1

            gromos_dihedrals.append( GromosBonded( [atom_index_1, atom_index_2, atom_index_3, atom_index_4], dihedral_type_index ) )

            basic_output_str ="%7i%7i%7i%7i%5i" % ( atom_index_1, atom_index_2, atom_index_3, atom_index_4, dihedral_type_index )            
            print (basic_output_str)
    print("END")

def _FindForceFieldTypes( atom, forcefield ):

    # test if ALL data is present:
    if (atom.type_name is None or
        atom.vdw_type is None or
        atom.mass_type is None or
        atom.charge_group is None): 

        raise LieTopologyException("WriteGromosTopology", "Writing atom %s->%s requires at least\
                                    type_name, mass_type, vdw_type and charge_group entries"\
                                    % ( molecule.key, atom.key ) ) 

    # all of the force field types could be references
    if (not isinstance(atom.vdw_type, VdwType) or
        not isinstance(atom.mass_type, MassType)):

        raise LieTopologyException("WriteGromosTopology", "Force field references for %s->%s should be pre-resolved"\
                                    % ( molecule.key, atom.key ) ) 

    charge = None

    # special handle for charges
    if atom.coulombic_type is not None:
        if not isinstance(atom.coulombic_type, CoulombicType):
            raise LieTopologyException("WriteGromosTopology", "Force field references for %s->%s should be pre-resolved"\
                                    % ( molecule.key, atom.key ) ) 
        
        charge = atom.coulombic_type.charge

    # charge override
    if atom.charge is not None:
        charge = atom.charge
    
    if charge is None:
        raise LieTopologyException("WriteGromosTopology", "No charge assignment for %s->%s"\
                                    % ( molecule.key, atom.key ) )
        
    mass = atom.mass_type.mass
    vdw_index = forcefield.vdwtypes.indexOf(atom.vdw_type.key) + 1 # +1 as gromos starts from 1

    # negative numbers indicate not found
    if vdw_index < 0:
        raise LieTopologyException("WriteGromosTopology", "Could not find vdw_type %s for atom %s->%s"\
                                    % ( atom.vdw_type.key, molecule.key, atom.key ) )  

    return mass, charge, vdw_index

def _WriteSoluteAtoms( solute_group, forcefield, bonded_graph, atom_to_graphid ):
    
    molecule_number=1

    print("SOLUTEATOM")
    for molecule_key, molecule in solute_group.molecules.items():
        
        explicit_exclusions = dict()
        for explicit_exclusion in molecule.exclusions:
                    
            atom_references = explicit_exclusion.atom_references
            
            if  not isinstance(atom_references[0], Atom) or\
                not isinstance(atom_references[1], Atom):
                raise LieTopologyException("WriteGromosTopology", "The atom indices for explicit exclusions should have been resolve to Atom links" )
            
            atom_i = atom_references[0].internal_index
            atom_j = atom_references[1].internal_index

            if not atom_i in explicit_exclusions:
                explicit_exclusions[atom_i] = set()
            
            explicit_exclusions[atom_i].add( atom_j )

        for atom_key, atom in molecule.atoms.items():

            internal_index = atom.internal_index
            nid = atom_to_graphid[internal_index]
            exclu_neighbours_set, neighbours_1_4_set = FindExplicitPairs( nid, bonded_graph )

            if internal_index in explicit_exclusions:
                exclu_neighbours_set.update( explicit_exclusions[internal_index] )
                neighbours_1_4_set.difference_update( exclu_neighbours_set )

            exclu_neighbours_str = ""
            exclu_count = 0 
            for exclu_atom in sorted(list(exclu_neighbours_set)):
                if exclu_atom > internal_index:
                    if exclu_count == 6:
                        exclu_neighbours_str += "\n"

                    exclu_neighbours_str += " %5i" % ( exclu_atom  + 1 )
                    exclu_count+=1

            neighbours_1_4_str = ""
            n1_4_count = 0
            for n1_4_atom in sorted(list(neighbours_1_4_set)):
                if n1_4_atom > internal_index:
                    neighbours_1_4_str += " %5i" % ( n1_4_atom  + 1)
                    n1_4_count += 1
            
            mass, charge, vdw_index = _FindForceFieldTypes( atom, forcefield )

            basic_output_str ="%6i %4i %4s %3i %8.5f %8.5f %2i %5i %s\n%47i %s" % ( internal_index+1, molecule_number, atom.type_name, 
                                                                                    vdw_index, mass, charge, atom.charge_group, 
                                                                                    exclu_count, exclu_neighbours_str,
                                                                                    n1_4_count, neighbours_1_4_str )   
            
            print (basic_output_str)
        molecule_number+=1
    print("END")

def WriteGromosTopology( ofstream, topology, forcefield, mass_of_hydrogen = 1.008 ):

    # Make sure the topology is force field resolved
    topology.ResolveForceFieldReferences( forcefield )

    solute_group = topology.GroupByKey("solute")

    # make sure its refererence resolved
    for molecule in solute_group.molecules.values():
        molecule.ResolveReferences(topology)

    if not solute_group:
        raise LieTopologyException("WriteGromosTopology", "Could not find a group named solute")

    bonded_graph, atom_index_to_graphid = GenerateBondedGraph( solute_group )

    _WriteSoluteAtoms( solute_group, forcefield, bonded_graph, atom_index_to_graphid )
    #_WriteSoluteBonds( solute_group, forcefield, mass_of_hydrogen )
    #_WriteSoluteAngles( solute_group, forcefield, mass_of_hydrogen )
    #_WriteSoluteImpropers( solute_group, forcefield, mass_of_hydrogen )
    #_WriteSoluteDihedrals( solute_group, forcefield, mass_of_hydrogen )
