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

def _ParseVoid(line, bookKeeping, structures):

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

       lastTopology.AddGroup( name=chain, chain_id=chain )

    lastChain = lastTopology.groups.back()

    # test of we need to add a new residue
    if len(lastChain.molecules) == 0 or\
       residue_number != lastChain.molecules[-1].identifier:

       lastChain.AddMolecule( name=residue_name, identifier=residue_number )

    lastResidue = lastChain.molecules[-1]
    lastResidue.AddAtom( name = atom_name, element = element, identifier = atom_number,\
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
    
    if not isinstance( lastStructure.coordinates, np.ndarray ):
        lastStructure.coordinates = np.array([x, y, z])

    else:
        np.append(lastStructure.coordinates,[x, y, z])

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


def ParsePdb( ifstream ):
    
    # Parser map
    parseFunctions = dict()
    parseFunctions["HEADER"]  = _ParseVoid
    parseFunctions["OBSLTE"]  = _ParseVoid
    parseFunctions["TITLE"]   = _ParseVoid
    parseFunctions["SPLT"]    = _ParseVoid
    parseFunctions["CAVEAT"]  = _ParseVoid
    parseFunctions["COMPND"]  = _ParseVoid
    parseFunctions["SOURCE"]  = _ParseVoid
    parseFunctions["KEYWDS"]  = _ParseVoid
    parseFunctions["EXPDTA"]  = _ParseVoid
    parseFunctions["NUMMDL"]  = _ParseVoid
    parseFunctions["MDLTYP"]  = _ParseVoid
    parseFunctions["AUTHOR"]  = _ParseVoid
    parseFunctions["REVDAT"]  = _ParseVoid
    parseFunctions["SPRSDE"]  = _ParseVoid
    parseFunctions["JRNL"]    = _ParseVoid
    parseFunctions["REMARKS"] = _ParseVoid
    parseFunctions["DBREF"]   = _ParseVoid
    parseFunctions["DBREF1"]  = _ParseVoid 
    parseFunctions["DBREF2"]  = _ParseVoid
    parseFunctions["SEQADV"]  = _ParseVoid
    parseFunctions["SEQRES"]  = _ParseVoid
    parseFunctions["MODRES"]  = _ParseVoid
    parseFunctions["HET"]     = _ParseVoid
    parseFunctions["FORMUL"]  = _ParseVoid
    parseFunctions["HETNAM"]  = _ParseVoid 
    parseFunctions["HETSYN"]  = _ParseVoid
    parseFunctions["HELIX"]   = _ParseVoid
    parseFunctions["SHEET"]   = _ParseVoid
    parseFunctions["SSBOND"]  = _ParseVoid
    parseFunctions["LINK"]    = _ParseVoid
    parseFunctions["CISPEP"]  = _ParseVoid
    parseFunctions["SITE"]    = _ParseVoid
    parseFunctions["CRYST1"]  = _ParseVoid
    parseFunctions["MTRIXn"]  = _ParseVoid
    parseFunctions["ORIGXn"]  = _ParseVoid
    parseFunctions["SCALEn"]  = _ParseVoid
    parseFunctions["MODEL"]   = _ParseVoid
    parseFunctions["ATOM"]    = _ParseAtom
    parseFunctions["ANISOU"]  = _ParseVoid
    parseFunctions["TER"]     = _ParseVoid
    parseFunctions["HETATM"]  = _ParseAtom
    parseFunctions["ENDMDL"]  = _ParseVoid
    parseFunctions["CONECT"]  = _ParseConnect
    parseFunctions["MASTER"]  = _ParseVoid
    parseFunctions["END"]     = _ParseVoid

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

    return structures        
