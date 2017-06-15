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

from lie_topology.common.exception import LieTopologyException
from lie_topology.forcefield.reference import ForceFieldReference
from lie_topology.forcefield.forcefield import CoulombicType, VdwType, MassType

def _WriteSoluteBonds( solute_group, forcefield ):

    pass

def _WriteSoluteAtoms( solute_group, forcefield ):

    
    ##
    ## DEBUG
    ##
    atom_number=1
    molecule_number=1

    print("SOLUTEATOM")

    for molecule_key, molecule in solute_group.molecules.items():
        for atom_key, atom in molecule.atoms.items():

            # test if ALL data is present:
            if (atom.type_name is None or
                atom.vdw_type is None or
                atom.mass_type is None or
                atom.coulombic_type is None or
                atom.charge_group is None): 

               raise LieTopologyException("WriteGromosTopology", "Writing atom %s->%s requires at least\
                                           type_name, mass_type, vdw_type, coulombic_type and charge_group entries"\
                                           % ( molecule.key, atom.key ) ) 

            # all of the force field types could be references
            if (not isinstance(atom.vdw_type, VdwType) or
                not isinstance(atom.mass_type, MassType) or
                not isinstance(atom.coulombic_type, CoulombicType)):

                raise LieTopologyException("WriteGromosTopology", "Force field references for %s->%s should be pre-resolved"\
                                           % ( molecule.key, atom.key ) ) 

            
            mass = atom.mass_type.mass
            charge = atom.coulombic_type.charge
            vdw_index = forcefield.vdwtypes.indexOf(atom.vdw_type.key) + 1 # +1 as gromos starts from 1

            basic_output_str ="%6i %4i %4s %3i %8.5f %8.5f %2i" % ( atom_number, molecule_number, atom.type_name, 
                                                                    vdw_index, mass, charge, atom.charge_group )
            
            print (basic_output_str)

            atom_number+=1
        molecule_number+=1

    print("END")

def WriteGromosTopology( ofstream, topology, forcefield ):

    # Make sure the topology is force field resolved
    topology.ResolveForceFieldReferences( forcefield )

    solute_group = topology.GroupByKey("solute")

    if not solute_group:
        raise LieTopologyException("WriteGromosTopology", "Could not find a group named solute")

    _WriteSoluteAtoms( solute_group, forcefield )
    _WriteSoluteBonds( solute_group, forcefield )
