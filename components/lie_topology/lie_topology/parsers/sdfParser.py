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

from copy import deepcopy

from lie_topology.common.exception   import LieTopologyException
from lie_topology.common.constants   import ANGSTROM_TO_NM
from lie_topology.molecule.structure import Structure
from lie_topology.molecule.topology  import Topology
from lie_topology.molecule.bond      import Bond

class Header(object):

    def __init__(self):

        self.n_atoms = 0
        self.n_bonds = 0
        self.n_lists = 0
        self.chiral  = 0
        self.n_stext = 0
        self.n_rcomp = 0
        self.n_reactants = 0
        self.n_products = 0
        self.n_inter = 0
        self.n_add_properties = 0
        self.ctab=None

def _ParseAtomV2( structure_molecule, line, coords ):

    if len(line) < 70:
        raise LieTopologyException("ParseSdf","Line length in sdf file is below expected 70 characters")
    
    x       = float( line[0:10].strip() )  * ANGSTROM_TO_NM
    y       = float( line[10:20].strip() ) * ANGSTROM_TO_NM
    z       = float( line[20:30].strip() ) * ANGSTROM_TO_NM
    element = line[31:34].strip()

    atom_number = structure_molecule.atoms.size() + 1
    atom_name   = "%s%i" % (element,atom_number)

    structure_molecule.AddAtom( key = atom_name, type_name = atom_name, identifier = atom_number, element=element )

    coords.append([x, y, z])


def _ParseBondV2( topology, line ):

    if len(line) < 22:
        raise LieTopologyException("ParseSdf","Line length in sdf bond block is below expected 22 characters")

    index_1 = int( line[0:3].strip() ) - 1
    index_2 = int( line[3:6].strip() ) - 1
    btype   = int( line[6:9].strip() )
    
    atom_1 = topology.atomByIndex( index_1 )
    atom_2 = topology.atomByIndex( index_2 )

    bond = Bond( atom_references=[atom_1,atom_2] )

    if btype >= 1 and btype <=3:
        bond.bond_order = btype

    elif btype == 4:
        bond.aromatic = True

    if atom_1.molecule is None:
        raise LieTopologyException("ParseSdf", "Attaching bond requires molecule links in the atoms" )

    atom_1.molecule.AddBond( bond )

def _ParseHeaderV2( line ):

    if len(line) < 40:
        raise LieTopologyException("ParseSdf","Line length in sdf file is below expected 40 characters")

    header = Header()
    header.n_atoms = int( line[0:3].strip() )
    header.n_bonds = int( line[3:6].strip() )
    header.n_lists = int( line[6:9].strip() )
    header.chiral  = int( line[12:15].strip() )
    header.n_stext = int( line[15:18].strip() )
    header.n_add_properties = int( line[30:33].strip() )
    header.ctab="V2000"

    if header.n_lists > 0 or\
       header.n_stext > 0:
       raise LieTopologyException("ParseSdf","List blocks and stxt entries not supported")
       
    return header

def _ParseHeaderV3( line ):  

    raise LieTopologyException("ParseSdf", "V3000 format currently unsupported, this is to be added at a later stage")

    return None

def ParseSdf( ifstream ):
    
    # Gro files contain a single structure 
    # and a single nameless group
    structures = []
    structure = Structure( topology=Topology(), description="")
    structure.topology.AddGroup( key=' ', chain_id=' ' )
    structure_group = structure.topology.groups.back() 
    structure_group.AddMolecule( key="MOL", type_name="MOL", identifier=1 )
    structure_molecule = structure_group.molecules.back()

    header = None
    n_comment = 0
    coords = []

    ## Uses occurance map to be order agnostic
    for line in ifstream:
        if len(line.strip()) == 0:
            continue

        if line.find("V2000") > 0:
            header = _ParseHeaderV2(line)

        elif line.find("V3000") > 0:
            header = _ParseHeaderV3(line)

        elif line.find("$$$$") >= 0:

            if header.n_atoms != 0:
                raise LieTopologyException("ParseSdf","Number of atoms promised does not match number of file lines" )

            if header.n_bonds != 0:
                raise LieTopologyException("ParseSdf","Number of bonds promised does not match number of file lines" )

            structure.coordinates = np.array( coords )
            structures.append(structure)
            
            header = None
            n_comment = 0
            coords = []
            structure = Structure( topology=Topology(), description="")
            structure.topology.AddGroup( key=' ', chain_id=' ' )
            structure_group = structure.topology.groups.back() 
            structure_group.AddMolecule( key="MOL", type_name="MOL", identifier=1 )
            structure_molecule = structure_group.molecules.back()

        elif header is None:
            structure.description+=line
            n_comment+=1
            
            if n_comment > 3:
                raise LieTopologyException("ParseSdf", "Found more than 3 comment lines before detecting the count line")

        elif header.n_atoms > 0:    
            if header.ctab == "V2000":
                _ParseAtomV2( structure_molecule, line, coords )

            header.n_atoms-=1

        elif header.n_bonds > 0:
            if header.ctab == "V2000":
                _ParseBondV2( structure.topology, line )

            header.n_bonds-=1

        else: 

            #  Void additional properties for now
            pass

    return structures