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

        self.name = None
        self.num_atoms = None
        self.num_bonds = None
        self.num_substruct = None
        self.num_features = None
        self.num_sets = None
        self.mol_type = None
        self.charge_type = None
        self.status_bit = None
        self.comment = None

def _void( line, header, structures ):

    # skip this info
    pass

def _ParseMolecule( line, headers, structures ):

    # Test and fill out data in order
    if len( headers ) == 0 or\
       headers[-1].name is None:
        header = Header()
        header.name = line
        headers.append(header)

        # create a new structure with a nameless group
        structure = Structure( topology=Topology(), key=header.name, description=header.comment)
        structure.topology.AddGroup( key=' ', chain_id=' ' )

        structures.append(structure)

    elif headers[-1].num_atoms is None:
        parts = line.split()

        headers[-1].num_atoms = int(parts[0])

        # as these statements could be optional we test one by one
        if len(parts) > 1:
            headers[-1].num_bonds = int(parts[1])
        
        if len(parts) > 2:
            headers[-1].num_substruct = int(parts[2])
        
        if len(parts) > 3:
            headers[-1].num_features = int(parts[3])

        if len(parts) > 4:
            headers[-1].num_sets = int(parts[4])
    
    elif headers[-1].mol_type is None:
        headers[-1].mol_type = line 

    elif headers[-1].charge_type is None:
        headers[-1].charge_type = line 
    
    elif headers[-1].status_bit is None:
        headers[-1].status_bit = line 
    
    elif headers[-1].comment is None:
        headers[-1].comment = line 

def _ValidateAndAppendTopology( lastStructure, atom_number, atom_name, residue_number, residue_name, sybyl,  element ):
    
    lastTopology = lastStructure.topology
    lastChain = lastTopology.groups.back()
    
    if residue_number is None:
        residue_number = 1

    molecule_name = "MOL"
    if residue_name is not None:
        molecule_name = "%s::%i" % ( residue_name, residue_number )

    


    # test of we need to add a new residue
    if len(lastChain.molecules) == 0 or\
       molecule_name != lastChain.molecules.back().key:

       lastChain.AddMolecule( key=molecule_name, type_name=residue_name, identifier=residue_number )

    lastResidue = lastChain.molecules.back()
    lastResidue.AddAtom( key = atom_name, type_name = atom_name, sybyl=sybyl, element = element, identifier = atom_number)

def _ParseAtom( line, headers, structures ):

    if len(structures) == 0:
        raise LieTopologyException("ParseMol2", "A MOLECULE section is required before an ATOM section")

    parts = line.split()
    
    if len(parts) < 6:
        raise LieTopologyException("ParseMol2", "At least 6 arguments required for an atom in the ATOM section")

    atom_number    = int(  parts[0])
    element        =       parts[1]
    x              = float(parts[2]) * ANGSTROM_TO_NM
    y              = float(parts[3]) * ANGSTROM_TO_NM
    z              = float(parts[4]) * ANGSTROM_TO_NM
    sybyl          =       parts[5]

    residue_number = None
    residue_name   = None
    charge         = None

    if len(parts) > 6:
        residue_number = int(parts[6])
    
    if len(parts) > 7:
        residue_name = parts[7]
    
    if len(parts) > 8:
        charge = float(parts[8])

    atom_name      = "%s%i" % ( element, atom_number )

    _ValidateAndAppendTopology( structures[-1], atom_number, atom_name, residue_number, residue_name, sybyl, element )
    
    if structures[-1].coordinates is None:
        structures[-1].coordinates = [[x, y, z]]

    else:
        structures[-1].coordinates.append( [x, y, z] )

def _ParseBond( line, headers, structures ):

    if len(structures) == 0:
        raise LieTopologyException("ParseMol2", "A MOLECULE section is required before an BOND section")

    parts = line.split()

    if len(parts) != 4 or\
       len(parts) != 5:

       raise LieTopologyException("ParseMol2", "Bond section requires 4 arguments or 5 with an optional status_bits")

    # -1 to convert to index
    index_1 = int( parts[0] ) - 1
    index_2 = int( parts[0] ) - 1

    topology = structures[-1].topology

    atom_1 = topology.atomByIndex( index_1 )
    atom_2 = topology.atomByIndex( index_2 )

    if atom_1.molecule is None:
        raise LieTopologyException("ParsePdb::_ParseConnect", "Attaching bond requires molecule links in the atoms" )

    atom_1.molecule.AddBond( Bond( atom_references=[atom_1,atom_2] ) )

def ParseMol2( ifstream ):
    
    parseFunctions = dict()
    parseFunctions["ALT_TYPE"] = _void
    parseFunctions["ANCHOR_ATOM"] = _void
    parseFunctions["ASSOCIATED_ANNOTATION"] = _void
    parseFunctions["ATOM"] = _ParseAtom
    parseFunctions["BOND"] = _void
    parseFunctions["CENTER_OF_MASS"] = _void
    parseFunctions["CENTROID"] = _void
    parseFunctions["COMMENT"] = _void
    parseFunctions["CRYSIN"] = _void
    parseFunctions["DICT"] = _void
    parseFunctions["DATA_FILE"] = _void
    parseFunctions["EXTENSION_POINT"] = _void
    parseFunctions["FF_PBC"] = _void
    parseFunctions["FFCON_ANGLE"] = _void
    parseFunctions["FFCON_DIST"] = _void
    parseFunctions["FFCON_MULTI"] = _void
    parseFunctions["FFCON_RANGE"] = _void
    parseFunctions["FFCON_TORSION"] = _void
    parseFunctions["LINE"] = _void
    parseFunctions["LSPLANE"] = _void
    parseFunctions["MOLECULE"] = _ParseMolecule
    parseFunctions["NORMAL"] = _void
    parseFunctions["QSAR_ALIGN_RULE"] = _void
    parseFunctions["RING_CLOSURE"] = _void
    parseFunctions["ROTATABLE_BOND"] = _void
    parseFunctions["SEARCH_DIST"] = _void
    parseFunctions["SEARCH_OPTIONS"] = _void
    parseFunctions["SET"] = _void
    parseFunctions["SUBSTRUCTURE"] = _void
    parseFunctions["U_FEAT"] = _void
    parseFunctions["UNITY_ATOM_ATTR"] = _void
    parseFunctions["UNITY_BOND_ATTR"] = _void

    # Gro files contain a single structure 
    # and a single nameless group
    structures = []

    coords = []
    headers = []
    section = None

    ## Uses occurance map to be order agnostic
    for line in ifstream:

        line = line.strip()
        if len(line) == 0:
            continue
        
        #test if we found a new header
        if line.find("@<TRIPOS>") >= 0:

            # assign the new section
            section = line.replace("@<TRIPOS>", "")
            continue

        if not section in parseFunctions:
            raise LieTopologyException("ParseMol2", "Unknown section '%s' " %(header))

        parseFunctions[section]( line, headers, structures )

    # make sure coordinates are nd_arrays now
    for i in range(0,len(structures)):
        structure = structures[i]
        header = headers[i]

        if structure.coordinates is not None:
            structure.coordinates = np.array( structure.coordinates )

        parsed_atom_count = structure.topology.atom_count

        # test if we found all promised counts
        if parsed_atom_count != header.num_atoms:
            raise LieTopologyException("ParseMol2", "Parsed atom count %i does not match input file count %i" % ( parsed_atom_count, header.num_atoms ))
        
        # TODO bond count

    return structures