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

def ParseGro( ifstream ):
    
    # Gro files contain a single structure 
    # and a single nameless group
    structures = []
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
            structure = Structure( description=line )
            structure.topology = Topology()
            structure.topology.AddGroup( key=' ', chain_id=' ' )
            structure_group = structure.topology.groups.back()
            structures.append(structure)
            

            coords = []
            velocities = []

            record_title = False
            
        elif record_n_atom:
            n_atom=int(line)
            record_n_atom = False
        
        elif n_atom == 0:
            # then record box info & reset


            record_title = True
            record_n_atom = True

        else: 

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

            # subtract expected atom
            n_atom-=1

    return structures