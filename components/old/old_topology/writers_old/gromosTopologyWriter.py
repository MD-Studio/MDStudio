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

    def __init__(self, indices, type_index ):

        self.indices = indices
        self.type_index = type_index

def _ContainsHydrogen( atom_references, mass_of_hydrogen ):

    for atom in atom_references:
        if atom.mass_type.mass == mass_of_hydrogen:
            return True
    
    return False


def _WriteToStream( ofstream, msg ):

    if False:
        ofstream.write( msg )
    else:
        print( msg )

def _WriteTitle( ofstream ):

    output_str = "TITLE\n"+\
    "Written by MD-Studio\n"+\
    "END"

    _WriteToStream( ofstream, output_str )

def _WritePhysConst( ofstream, phys_const ):

    output_str = ( "PHYSICALCONSTANTS\n"+\
    "# FPEPSI: 1.0/(4.0*PI*EPS0) (EPS0 is the permittivity of vacuum)\n"+\
    "{four_pi_eps0_i}\n"+\
    "# HBAR: Planck's constant HBAR = H/(2* PI)\n"+\
    "{plancks_constant}\n"+\
    "# SPDL: Speed of light (nm/ps)\n"+\
    "{speed_of_light}\n"+\
    "# BOLTZ: Boltzmann's constant kB\n"+\
    "{boltzmann_constant}\n"+\
    "END" ).format( four_pi_eps0_i=phys_const.four_pi_eps0_i,
                    plancks_constant=phys_const.plancks_constant,
                    speed_of_light=phys_const.speed_of_light,
                    boltzmann_constant=phys_const.boltzmann_constant)

    _WriteToStream( ofstream, output_str )

def _WriteVersion( ofstream ):

    output_str = "TOPVERSION\n"+\
    "2.0\n"+\
    "END"

    _WriteToStream( ofstream, output_str )

def _WriteAtomNames( ofstream, forcefield ):

    output_str = "ATOMTYPENAME\n"+\
    "# NRATT: number of van der Waals atom types\n"+\
    "%i\n" % ( len(forcefield.vdwtypes) )+\
    "# TYPE: atom type names\n"

    count = 0
    for atom_type in forcefield.vdwtypes.keys():
        if count % 10 == 0 and count != 0:
            output_str+="# %i\n" % (count)
        
        output_str += "%s\n" % ( atom_type )
        count+=1

    output_str += "END"
    _WriteToStream( ofstream, output_str )  

def _WriteMoleculeNames( ofstream, solute_group ):

    output_str = "RESNAME\n"+\
    "# NRAA2: number of residues in a solute molecule\n"+\
    "%i\n" % ( len(solute_group.molecules) )+\
    "# AANM: residue names\n"

    count = 0
    for molecule in solute_group.molecules.values():
        if count % 10 == 0 and count != 0:
            output_str+="# %i\n" % (count)
        
        output_str += "%s\n" % ( molecule.type_name )
        count+=1

    output_str += "END"
    _WriteToStream( ofstream, output_str )  

def _WriteBondTypes( ofstream, forcefield ):

    output_str = "BONDSTRETCHTYPE\n"+\
    "#  NBTY: number of covalent bond types\n"+\
    "%i\n" % (len(forcefield.bondtypes))+\
    "#  CB:  quartic force constant\n"+\
    "#  CHB: harmonic force constant\n"+\
    "#  B0:  bond length at minimum energy\n"+\
    "#         CB         CHB         B0\n"

    count = 0
    for bond_type in forcefield.bondtypes.values():
        if count % 10 == 0 and count != 0:
            output_str+="# %i\n" % (count)
        
        output_str += " %15.5e %15.5e %15.5e\n" % ( bond_type.fc_quartic, bond_type.fc_harmonic, bond_type.bond0 )
        count+=1

    output_str+="END"
    _WriteToStream( ofstream, output_str )  

def _WriteBondedSolution( ofstream, gromos_bondeds ):

    output_str = ""
    count = 0
    #for bonded in sorted(gromos_bondeds, key=lambda x: x.indices[0]):
    for bonded in gromos_bondeds:
        if count % 10 == 0 and count != 0:
            output_str+="# %i\n" % (count)
        
        for index in bonded.indices:
            output_str+="%7i" % (index+1)
        output_str += "%5i\n" % (bonded.type_index+1)
        count+=1
    _WriteToStream( ofstream, output_str )

def _WriteSoluteBonds( ofstream, solute_group, forcefield, mass_of_hydrogen ):

    gromos_bonds = []
    gromos_h_bonds = []

    for molecule_key, molecule in solute_group.molecules.items():
        for bond in molecule.bonds:
            
            # all of the force field types could be references
            if not isinstance(bond.forcefield_type, BondType):
                raise LieTopologyException("WriteGromosTopology", "Bond types should be pre-resolved" ) 
            
            bond_type_index = forcefield.bondtypes.indexOf(bond.forcefield_type.key)

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
            atom_index_1 = atom_references[0].internal_index
            atom_index_2 = atom_references[1].internal_index

            gromos_bonded = GromosBonded( [atom_index_1, atom_index_2], bond_type_index )

            if _ContainsHydrogen( atom_references, mass_of_hydrogen ):
                gromos_h_bonds.append( gromos_bonded )
            else:
                gromos_bonds.append( gromos_bonded )

    _WriteToStream( ofstream, "BONDH")
    _WriteToStream( ofstream, "#  NBONH: number of bonds involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % ( len(gromos_h_bonds) ) )
    _WriteToStream( ofstream, "#  IBH, JBH: atom sequence numbers of atoms forming a bond")
    _WriteToStream( ofstream, "#  ICBH: bond type code")
    _WriteToStream( ofstream, "#   IBH    JBH ICBH")
    _WriteBondedSolution( ofstream, gromos_h_bonds )
    _WriteToStream( ofstream, "END")

    _WriteToStream( ofstream, "BOND")
    _WriteToStream( ofstream, "#  NBON: number of bonds NOT involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % ( len(gromos_bonds) ) )
    _WriteToStream( ofstream, "#  IB, JB: atom sequence numbers of atoms forming a bond")
    _WriteToStream( ofstream, "#  ICB: bond type code")
    _WriteToStream( ofstream, "#    IB     JB  ICB")
    _WriteBondedSolution( ofstream, gromos_bonds )
    _WriteToStream( ofstream, "END")

    

def _WriteSoluteAngles( ofstream, solute_group, forcefield, mass_of_hydrogen ):

    gromos_angles = []
    gromos_h_angles = []

    for molecule_key, molecule in solute_group.molecules.items():
        for angle in molecule.angles:
            
            # all of the force field types could be references
            if not isinstance(angle.forcefield_type, AngleType):
                raise LieTopologyException("WriteGromosTopology", "Angle types should be pre-resolved" ) 
            
            angle_type_index = forcefield.angletypes.indexOf(angle.forcefield_type.key)

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
            atom_index_1 = atom_references[0].internal_index 
            atom_index_2 = atom_references[1].internal_index
            atom_index_3 = atom_references[2].internal_index 

            gromos_bonded = GromosBonded( [atom_index_1, atom_index_2, atom_index_3], angle_type_index )

            if _ContainsHydrogen( atom_references, mass_of_hydrogen ):
                gromos_h_angles.append( gromos_bonded )
            else:
                gromos_angles.append( gromos_bonded )

    
    _WriteToStream( ofstream, "BONDANGLEH")
    _WriteToStream( ofstream, "#  NTHEH: number of bond angles involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % (len(gromos_h_angles))) 
    _WriteToStream( ofstream, "#  ITH, JTH, KTH: atom sequence numbers")
    _WriteToStream( ofstream, "#    of atoms forming a bond angle in solute")
    _WriteToStream( ofstream, "#  ICTH: bond angle type code")
    _WriteToStream( ofstream, "#   ITH    JTH    KTH ICTH")
    _WriteBondedSolution( ofstream, gromos_h_angles )
    _WriteToStream( ofstream, "END")
    
    _WriteToStream( ofstream, "BONDANGLE")
    _WriteToStream( ofstream, "#  NTHE: number of bond angles NOT")
    _WriteToStream( ofstream, "#        involving H atoms in solute")
    _WriteToStream( ofstream, "2556")
    _WriteToStream( ofstream, "#  IT, JT, KT: atom sequence numbers of atoms")
    _WriteToStream( ofstream, "#     forming a bond angle")
    _WriteToStream( ofstream, "#  ICT: bond angle type code")
    _WriteToStream( ofstream, "#    IT     JT     KT  ICT")
    _WriteBondedSolution( ofstream, gromos_angles )
    _WriteToStream( ofstream, "END")

def _WriteSoluteImpropers( ofstream, solute_group, forcefield, mass_of_hydrogen ):

    gromos_impropers = []
    gromos_h_impropers = []

    for molecule_key, molecule in solute_group.molecules.items():
        for improper in molecule.impropers:
            
            # all of the force field types could be references
            if not isinstance(improper.forcefield_type, ImproperType):
                raise LieTopologyException("WriteGromosTopology", "improper types should be pre-resolved" ) 
            
            improper_type_index = forcefield.impropertypes.indexOf(improper.forcefield_type.key)

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
            atom_index_1 = atom_references[0].internal_index
            atom_index_2 = atom_references[1].internal_index 
            atom_index_3 = atom_references[2].internal_index
            atom_index_4 = atom_references[3].internal_index 

            gromos_bonded = GromosBonded( [atom_index_1, atom_index_2, atom_index_3, atom_index_4], improper_type_index )

            if _ContainsHydrogen( atom_references, mass_of_hydrogen ):
                gromos_h_impropers.append( gromos_bonded )
            else:
                gromos_impropers.append( gromos_bonded )

    _WriteToStream( ofstream, "IMPDIHEDRALH")
    _WriteToStream( ofstream, "#  NQHIH: number of improper dihedrals")
    _WriteToStream( ofstream, "#         involving H atoms in the solute")
    _WriteToStream( ofstream, "%i" % (len(gromos_h_impropers)))
    _WriteToStream( ofstream, "#  IQH,JQH,KQH,LQH: atom sequence numbers")
    _WriteToStream( ofstream, "#     of atoms forming an improper dihedral")
    _WriteToStream( ofstream, "#  ICQH: improper dihedral type code")
    _WriteToStream( ofstream, "#   IQH    JQH    KQH    LQH ICQH")
    _WriteBondedSolution( ofstream, gromos_h_impropers )
    _WriteToStream( ofstream, "END")

    _WriteToStream( ofstream, "IMPDIHEDRAL")
    _WriteToStream( ofstream, "#  NQHI: number of improper dihedrals NOT")
    _WriteToStream( ofstream, "#    involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % (len(gromos_impropers)))
    _WriteToStream( ofstream, "#  IQ,JQ,KQ,LQ: atom sequence numbers of atoms")
    _WriteToStream( ofstream, "#    forming an improper dihedral")
    _WriteToStream( ofstream, "#  ICQ: improper dihedral type code")
    _WriteToStream( ofstream, "#    IQ     JQ     KQ     LQ  ICQ")
    _WriteBondedSolution( ofstream, gromos_impropers )
    _WriteToStream( ofstream, "END")

def _WriteSoluteDihedrals( ofstream, solute_group, forcefield, mass_of_hydrogen ):

    gromos_dihedrals = []
    gromos_h_dihedrals = []

    for molecule_key, molecule in solute_group.molecules.items():
        for dihedral in molecule.dihedrals:
            
            # all of the force field types could be references
            if not isinstance(dihedral.forcefield_type, DihedralType):
                raise LieTopologyException("WriteGromosTopology", "dihedral types should be pre-resolved" ) 
            
            dihedral_type_index = forcefield.dihedraltypes.indexOf(dihedral.forcefield_type.key)

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
            atom_index_1 = atom_references[0].internal_index
            atom_index_2 = atom_references[1].internal_index 
            atom_index_3 = atom_references[2].internal_index 
            atom_index_4 = atom_references[3].internal_index

            gromos_bonded = GromosBonded( [atom_index_1, atom_index_2, atom_index_3, atom_index_4], dihedral_type_index ) 

            if _ContainsHydrogen( atom_references, mass_of_hydrogen ):
                gromos_h_dihedrals.append( gromos_bonded )
            else:
                gromos_dihedrals.append( gromos_bonded )

    _WriteToStream( ofstream, "DIHEDRALH")
    _WriteToStream( ofstream, "#  NPHIH: number of dihedrals involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % (len(gromos_h_dihedrals)))
    _WriteToStream( ofstream, "#  IPH, JPH, KPH, LPH: atom sequence numbers")
    _WriteToStream( ofstream, "#    of atoms forming a dihedral")
    _WriteToStream( ofstream, "#  ICPH: dihedral type code")
    _WriteToStream( ofstream, "#   IPH    JPH    KPH    LPH ICPH")
    _WriteBondedSolution( ofstream, gromos_h_dihedrals )
    _WriteToStream( ofstream, "END")
    _WriteToStream( ofstream, "DIHEDRAL")
    _WriteToStream( ofstream, "#  NPHI: number of dihedrals NOT involving H atoms in solute")
    _WriteToStream( ofstream, "%i" % (len(gromos_dihedrals)))
    _WriteToStream( ofstream, "#  IP, JP, KP, LP: atom sequence numbers")
    _WriteToStream( ofstream, "#     of atoms forming a dihedral")
    _WriteToStream( ofstream, "#  ICP: dihedral type code")
    _WriteToStream( ofstream, "#    IP     JP     KP     LP  ICP")
    _WriteBondedSolution( ofstream, gromos_dihedrals )
    _WriteToStream( ofstream, "END")

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

def _WriteSoluteAtoms( ofstream, solute_group, forcefield, bonded_graph, atom_to_graphid ):
    
    molecule_number=1

    # start by gathering cg's
    # we need this as the loop requires an look_ahead
    charge_group_indices = []
    charge_group_offset = 0
    for molecule in solute_group.molecules.values():

        last_cg = charge_group_offset
        for atom in molecule.atoms.values():

            last_cg = atom.charge_group
            charge_group_indices.append( charge_group_offset+last_cg )

        charge_group_offset=charge_group_offset+last_cg+1

    output_str = "SOLUTEATOM\n"+\
    "#   NRP: number of solute atoms\n"+\
    "%5i\n" % ( solute_group.atom_count )+\
    "#  ATNM: atom number\n"+\
    "#  MRES: residue number\n"+\
    "#  PANM: atom name of solute atom\n"+\
    "#   IAC: integer (van der Waals) atom type code\n"+\
    "#  MASS: mass of solute atom\n"+\
    "#    CG: charge of solute atom\n"+\
    "#   CGC: charge group code (0 or 1)\n"+\
    "#   INE: number of excluded atoms\n"+\
    "# INE14: number of 1-4 interactions\n"+\
    "# ATNM MRES PANM IAC     MASS       CG  CGC INE\n"+\
    "#                                           INE14\n"

    atom_it=0
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
                        exclu_neighbours_str += "\n" + " " * 47 

                    exclu_neighbours_str += " %5i" % ( exclu_atom  + 1 )
                    exclu_count+=1

            neighbours_1_4_str = ""
            n1_4_count = 0
            for n1_4_atom in sorted(list(neighbours_1_4_set)):
                if n1_4_atom > internal_index:
                    neighbours_1_4_str += " %5i" % ( n1_4_atom  + 1)
                    n1_4_count += 1
            
            mass, charge, vdw_index = _FindForceFieldTypes( atom, forcefield )
            gromos_cg = 1 if ( atom_it+1 == len(charge_group_indices) or\
                               charge_group_indices[atom_it] != charge_group_indices[atom_it+1] )\
                          else 0

            output_str += "%6i %4i %4s %3i %8.5f %8.5f %2i %5i%s\n%47i%s\n" % ( internal_index+1, molecule_number, atom.type_name, 
                                                                                vdw_index, mass, charge, gromos_cg, 
                                                                                exclu_count, exclu_neighbours_str,
                                                                                n1_4_count, neighbours_1_4_str )   

            atom_it+=1

        molecule_number+=1

    output_str += "END"
    _WriteToStream( ofstream, output_str)



def WriteGromosTopology( ofstream, topology, forcefield, physical_constants, mass_of_hydrogen = 1.008 ):

    # Make sure the topology is force field resolved
    topology.ResolveForceFieldReferences( forcefield )

    solute_group = topology.GroupByKey("solute")

    # make sure its refererence resolved
    for molecule in solute_group.molecules.values():
        molecule.ResolveReferences(topology)

    if not solute_group:
        raise LieTopologyException("WriteGromosTopology", "Could not find a group named solute")

    bonded_graph, atom_index_to_graphid = GenerateBondedGraph( solute_group )

    _WriteTitle( ofstream )
    _WritePhysConst( ofstream, physical_constants )
    _WriteVersion( ofstream )
    _WriteAtomNames( ofstream, forcefield )
    _WriteMoleculeNames( ofstream, solute_group )
    _WriteSoluteAtoms( ofstream, solute_group, forcefield, bonded_graph, atom_index_to_graphid )
    _WriteBondTypes( ofstream, forcefield )
    _WriteSoluteBonds( ofstream, solute_group, forcefield, mass_of_hydrogen )
    _WriteSoluteAngles( ofstream, solute_group, forcefield, mass_of_hydrogen )
    _WriteSoluteImpropers( ofstream, solute_group, forcefield, mass_of_hydrogen )
    _WriteSoluteDihedrals( ofstream, solute_group, forcefield, mass_of_hydrogen )
