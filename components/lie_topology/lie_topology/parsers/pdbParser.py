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

class PdbBookKeeping(object):

    def __init__(self):

        pass

def _Void(line, bookKeeping, structures):

    # voids currently unsupported entries
    pass

def _ValidateAndAppendTopology( lastStructure, atom_number, atom_name, residue_number, residue_name, chain,\
                                occupancy, b_factor, element ):
    
    
    lastTopology = lastStructure.topology

    # test if there is an active topology
    if not lastTopology:
        lastTopology = Topology()
        lastStructure.topology = lastTopology

    # test if we need to add a new chain
    if len(lastTopology.groups) == 0 or\
       chain != lastTopology.groups.back().chain_id:

       lastTopology.AddGroup( key=chain, chain_id=chain )

    lastChain = lastTopology.groups.back()

    molecule_name = "%s::%i" % ( residue_name, residue_number )

    # test of we need to add a new residue
    if len(lastChain.molecules) == 0 or\
       molecule_name != lastChain.molecules.back().key:

       lastChain.AddMolecule( key=molecule_name, type_name=residue_name, identifier=residue_number )

    lastResidue = lastChain.molecules.back()
    lastResidue.AddAtom( key = atom_name, type_name = atom_name, element = element, identifier = atom_number,\
                         occupancy = occupancy, b_factor = b_factor  )

def _ParseAtom(line, bookKeeping, structures):

    atom_number    = int(   line[6:11].strip()  )
    atom_name      =        line[12:16].strip()
    residue_name   =        line[17:21].strip()
    chain          =        line[21:22].strip()
    residue_number = int(   line[22:26].strip() )
    x              = float( line[30:38].strip() ) * ANGSTROM_TO_NM
    y              = float( line[38:46].strip() ) * ANGSTROM_TO_NM
    z              = float( line[46:54].strip() ) * ANGSTROM_TO_NM
    occupancy      = float( line[54:60].strip() )
    b_factor       = float( line[60:66].strip() )  
    element        =        line[76:78].strip()
    charge         =        line[78:80].strip() 
    
    # Test if there is an active structure
    if len(structures) == 0:
        structures.append( Structure() )

    lastStructure = structures[-1]

    _ValidateAndAppendTopology( lastStructure, atom_number, atom_name, residue_number, residue_name, chain,\
                                occupancy, b_factor, element )
    
    if lastStructure.coordinates is None:
        lastStructure.coordinates = [[x, y, z]]

    else:
        lastStructure.coordinates.append( [x, y, z] )

def _AppendBond( topology, atomIndex1, atomIndex2 ):

    atom_1 = topology.atomByIndex( atomIndex1 )
    atom_2 = topology.atomByIndex( atomIndex2 )

    print( atom_1, atom_2 )

def _ParseConnect(line, bookKeeping, structures):

    from_index_str = line[6:11].strip()
    to_index1_str  = line[11:16].strip()
    to_index2_str  = line[16:21].strip()
    to_index3_str  = line[21:26].strip()
    to_index4_str  = line[26:31].strip()

    if len(structures) == 0:
        raise LieTopologyException("ParsePdb::_ParseConnect", "No structures present" )
    
    lastStructure = structures[-1]
    lastTopology = lastStructure.topology

    # test if there is an active topology
    if not lastTopology:
        raise LieTopologyException("ParsePdb::_ParseConnect", "Expect a valid structure topology" )

    if len(from_index_str) == 0:
        raise LieTopologyException("ParsePdb::_ParseConnect", "Expect atom serial number in column 7-11" )

    if len(to_index1_str) == 0:
        raise LieTopologyException("ParsePdb::_ParseConnect", "Expect atom serial number in column 12-16" )

    #  Counting starts from 1, so -1
    from_index = int( from_index_str ) - 1
    to_index1  = int( to_index1_str ) - 1

    _AppendBond( lastTopology, from_index, to_index1 )

    # Only if more bods are defined do we use these

    if len(to_index2_str) > 0:
        to_index2  = int( to_index2_str ) - 1
        _AppendBond( lastStructure, from_index, to_index2 )

    if len(to_index3_str) > 0:
        to_index3  = int( to_index3_str ) - 1
        _AppendBond( lastStructure, from_index, to_index3 )

    if len(to_index4_str) > 0:
        to_index4  = int( to_index4_str ) - 1
        _AppendBond( lastStructure, from_index, to_index4 )


def _ParseCrystal(line, bookKeeping, structures):

    side_a  = float( line[6:15].strip() )
    side_b  = float( line[15:24].strip() )
    side_c  = float( line[24:33].strip() )
    alpha   = float( line[33:40].strip() )
    beta    = float( line[40:47].strip() )
    gamma   = float( line[47:54].strip() )

    space_group = line[55:66].strip()
    z_value = line[66:70].strip()

    if len(structures) == 0:
        raise LieTopologyException("ParsePdb::_ParseCrystal", "No structures present" )
    
    lastStructure = structures[-1]

    lastStructure.lattice = Lattice()

    # lenghts of the a,b & c edges, should be a vec3
    lastStructure.lattice.edge_lenghts = [ side_a, side_b, side_c ]
    lastStructure.lattice.edge_angles = [ alpha, beta, gamma ]
    lastStructure.lattice.rotation = [ 0.0, 0.0, 0.0 ]
    lastStructure.lattice.offset = [ 0.0, 0.0, 0.0 ]

def ParsePdb( ifstream ):
    
    # Parser map
    parseFunctions = dict()
    parseFunctions["HEADER"]  = _Void
    parseFunctions["OBSLTE"]  = _Void
    parseFunctions["TITLE"]   = _Void
    parseFunctions["SPLT"]    = _Void
    parseFunctions["CAVEAT"]  = _Void
    parseFunctions["COMPND"]  = _Void
    parseFunctions["SOURCE"]  = _Void
    parseFunctions["KEYWDS"]  = _Void
    parseFunctions["EXPDTA"]  = _Void
    parseFunctions["NUMMDL"]  = _Void
    parseFunctions["MDLTYP"]  = _Void
    parseFunctions["AUTHOR"]  = _Void
    parseFunctions["REVDAT"]  = _Void
    parseFunctions["SPRSDE"]  = _Void
    parseFunctions["JRNL"]    = _Void
    parseFunctions["REMARKS"] = _Void
    parseFunctions["DBREF"]   = _Void
    parseFunctions["DBREF1"]  = _Void 
    parseFunctions["DBREF2"]  = _Void
    parseFunctions["SEQADV"]  = _Void
    parseFunctions["SEQRES"]  = _Void
    parseFunctions["MODRES"]  = _Void
    parseFunctions["HET"]     = _Void
    parseFunctions["FORMUL"]  = _Void
    parseFunctions["HETNAM"]  = _Void 
    parseFunctions["HETSYN"]  = _Void
    parseFunctions["HELIX"]   = _Void
    parseFunctions["SHEET"]   = _Void
    parseFunctions["SSBOND"]  = _Void
    parseFunctions["LINK"]    = _Void
    parseFunctions["CISPEP"]  = _Void
    parseFunctions["SITE"]    = _Void
    parseFunctions["CRYST1"]  = _ParseCrystal
    parseFunctions["MTRIXn"]  = _Void
    parseFunctions["ORIGXn"]  = _Void
    parseFunctions["SCALEn"]  = _Void
    parseFunctions["MODEL"]   = _Void
    parseFunctions["ATOM"]    = _ParseAtom
    parseFunctions["ANISOU"]  = _Void
    parseFunctions["TER"]     = _Void
    parseFunctions["HETATM"]  = _ParseAtom
    parseFunctions["ENDMDL"]  = _Void
    parseFunctions["CONECT"]  = _ParseConnect
    parseFunctions["MASTER"]  = _Void
    parseFunctions["END"]     = _Void

    bookKeeping = PdbBookKeeping()

    structures = []
    
    ## Uses occurance map to be order agnostic
    for line in ifstream:
        
        # assure line length to 80
        toadd = max( 0, 80 - len(line) )
        line += " " * toadd
        
        # find what record this is
        blockName = line[0:6].strip()

        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParsePdb", "Unknown pdb block %s" % (blockName) )
        
        parseFunctions[blockName]( line, bookKeeping, structures )

    # make sure coordinates are nd_arrays now
    for structure in structures:
        structure.coordinates = np.array( structure.coordinates )


    return structures        
