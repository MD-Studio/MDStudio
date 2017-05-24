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


import sys
import os
import numpy as np

from lie_topology.common.exception   import LieTopologyException
from lie_topology.molecule.structure import Structure
from lie_topology.molecule.topology  import Topology
from lie_topology.molecule.crystal   import BoxVectorsToLattice

def _ParseAtom( structure_group, line, coords, velocities ):

    if len(line) < 68:
        raise LieTopologyException("ParseGro","Line length in gro file is below expected 68 characters")

    residue_number = int(   line[0:5].strip() )
    residue_name   =        line[5:10].strip()
    atom_name      =        line[10:15].strip()
    atom_number    = int(   line[15:20].strip() )
    
    x              = float( line[20:28].strip() ) 
    y              = float( line[28:36].strip() ) 
    z              = float( line[36:44].strip() )

    vx             = float( line[44:52].strip() ) 
    vy             = float( line[52:60].strip() ) 
    vz             = float( line[60:68].strip() )

    molecule_name = "%s::%i" % ( residue_name, residue_number )

    # test of we need to add a new residue
    if len(structure_group.molecules) == 0 or\
        molecule_name != structure_group.molecules.back().key:

        structure_group.AddMolecule( key=molecule_name, type_name=residue_name, identifier=residue_number )

    lastResidue = structure_group.molecules.back()
    lastResidue.AddAtom( key = atom_name, type_name = atom_name, identifier = atom_number )

    coords.append([x, y, z])
    velocities.append([vx, vy, vz])

def _ParseCrystal( structure, line ):

    parts = line.split()

    if len(parts) < 3:
        raise LieTopologyException("ParseGro","Crystal definitions needs at least v1(x) v2(y) v3(z) entries")

    if len(parts) > 3 and len(parts) != 9:
        raise LieTopologyException("ParseGro","Extended crystal definition needs 9 entries; v1(x) v2(y) v3(z) v1(y) v1(z) v2(x) v2(z) v3(x) v3(y)")
        
    v1 = [0.0, 0.0, 0.0]
    v2 = [0.0, 0.0, 0.0]
    v3 = [0.0, 0.0, 0.0]

    # matrix diagonal
    v1[0] = float(parts[0])
    v2[1] = float(parts[1])
    v3[2] = float(parts[2])

    if len(parts) > 3:
        v1[1] = float(parts[3])
        v1[2] = float(parts[4])
        v2[0] = float(parts[5])
        
        v2[2] = float(parts[6])
        v3[0] = float(parts[7])
        v3[1] = float(parts[8])
    

    structure.lattice = BoxVectorsToLattice(v1, v2, v3)

def ParseGro( ifstream ):
    
    # Gro files contain a single structure 
    # and a single nameless group
    structures = []
    structure = None
    structure_group = None 

    record_title = True
    record_n_atom = True

    n_atom = 0
    coords = []
    velocities = []

    ## Uses occurance map to be order agnostic
    for line in ifstream:

        if len(line.strip()) == 0:
            continue

        if record_title:

            #start adding a enew structure
            structure = Structure( description=line, topology=Topology() )
            structure.topology.AddGroup( key=' ', chain_id=' ' )
            structure_group = structure.topology.groups.back()
            structures.append(structure)

            record_title = False
            
        elif record_n_atom:
            n_atom=int(line)
            record_n_atom = False
        
        elif n_atom == 0:

            _ParseCrystal( structure, line )

            structure.coordinates = np.array( coords )
            structure.velocities  = np.array( velocities )

            # then record box info & reset
            record_title = True
            record_n_atom = True

            coords = []
            velocities = []

        else: 

            _ParseAtom( structure_group, line, coords, velocities )
            
            # subtract expected atom
            n_atom-=1

    if n_atom != 0 or structures[-1].lattice is None:
        raise LieTopologyException("ParseGro","Number of atoms promised does not match number of file lines" )

    return structures