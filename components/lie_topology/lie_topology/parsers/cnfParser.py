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

from lie_topology.common.tokenizer   import Tokenizer
from lie_topology.common.exception   import LieTopologyException
from lie_topology.molecule.structure import Structure, Time
from lie_topology.molecule.topology  import Topology
from lie_topology.molecule.crystal   import Lattice
from lie_topology.molecule.group     import Group

def _AppendTopological( activeTopology, resNum, resName, atomName, atomNum ):

    print ( resNum )
    activeGroup = activeTopology.GetGroup("solute")

    if not activeGroup:
        
        activeTopology.AddGroup( name="solute"  )
        activeGroup = activeTopology.GetGroup("solute")

        #as this is a new group we are sure that this doesnt contain a residue yet
        activeGroup.AddSolute( name=resName, identifier=resNum )

    lastResidue = activeGroup.GetSoluteByIndex( -1 )

    print ( resName, lastResidue.name, resNum, lastResidue.identifier)

    if resName != lastResidue.name or\
       resNum != lastResidue.identifier:

        activeGroup.AddSolute( name=resName, identifier=resNum )
        lastResidue = activeGroup.GetSoluteByIndex( -1 )
    
    lastResidue.AddAtom( name=atomName, identifier=atomNum )

def _ParseTitle(block, structure):

    structure.description = ' '.join(block)

def _ParseTimeStep(block, structure):

    modelnr = int( block[0] )
    simtime = float( block[1] )

    #currently not used
    structure.step = Time()
    structure.step.model_number = modelnr
    structure.step.time = simtime
 
# All extended blocks (position, force & velocity are ordered in a similar manner),
# Use this parser to gather all the data
def _ParseTopologicalBlock(block, structure):

    vectors = []
    activeTopology = Topology()

    # If the structure does not have a topology yet
    for str_resNum, resName, atomName, str_atomNum, str_x, str_y, str_z in zip( block[0::7], block[1::7], 
                                                                                block[2::7], block[3::7], 
                                                                                block[4::7], block[5::7], 
                                                                                block[6::7]):	
        
        x = float(str_x)
        y = float(str_y)
        z = float(str_z)
        
        #if we want to record topological information
        if activeTopology:

            resNum = int(str_resNum)
            atomNum = int(str_atomNum)

            _AppendTopological( activeTopology, resNum, resName, atomName, atomNum )
        
        # array of coords
        vectors.append([x,y,z])

    return activeTopology, vectors

# Use this to parse block that only contain vectors
def _ParseFloatVectorBlock(block, structure):

    vectors = []

    # If the structure does not have a topology yet
    for str_x, str_y, str_z in zip( block[0::3], block[1::3], block[2::3] ):	
        
        x = float(str_x)
        y = float(str_y)
        z = float(str_z)

        # array of coords
        vectors.append([x,y,z])

    return vectors

# Use this to parse block that only contain vectors
def _ParseIntVectorBlock(block, structure):

    vectors = []

    # If the structure does not have a topology yet
    for str_x, str_y, str_z in zip( block[0::3], block[1::3], block[2::3] ):	
        
        x = int(str_x)
        y = int(str_y)
        z = int(str_z)

        # array of coords
        vectors.append([x,y,z])

    return vectors

def _ParsePosition(block, structure):
    
    activeTopology, vectors = _ParseTopologicalBlock(block, structure)

    structure.coordinates = np.array( vectors )

    # save topology if not yet there
    if not structure.topology:
        structure.topology = activeTopology

def _ParseLatticeShifts(block, structure):

    vectors = _ParseIntVectorBlock(block, structure)

    structure.lattice_shifs = np.array( vectors )
    
def _ParseVelocity(block, structure):

    activeTopology, vectors = _ParseTopologicalBlock(block, structure)

    structure.velocities = np.array( vectors )

    # save topology if not yet there
    if not structure.topology:
        structure.topology = activeTopology
    
def _ParseGenbox(block, structure):

    lx = float( block[1] )
    ly = float( block[2] )
    lz = float( block[3] )

    alpha = float( block[4] )
    beta  = float( block[5] )
    gamma = float( block[6] )

    phi   = float( block[7] )
    theta = float( block[8] )
    psi   = float( block[9] )

    ox    = float( block[10] )
    oy    = float( block[11] )
    oz    = float( block[12] )
    
    structure.lattice = Lattice()

    # lenghts of the a,b & c edges, should be a vec3
    structure.lattice.edge_lenghts = [ lx, ly, lz ]
    structure.lattice.edge_angles = [ alpha, beta, gamma ]
    structure.lattice.rotation = [ phi, theta, psi ]
    structure.lattice.offset = [ ox, oy, oz ]

def _ParseCosDiplacements(block, structure):
    
    vectors = _ParseFloatVectorBlock(block, structure)

    structure.cos_offsets = np.array( vectors )

def _ParseFreeForce(block, structure):

    activeTopology, vectors = _ParseTopologicalBlock(block, structure)

    # Two options
    # If it exists already do an add.
    # Otherwise assign
    if structure.force:
        structure.force = np.add( structure.force, np.array( vectors ) );
    else:
        structure.force = np.array( vectors )

    # save topology if not yet there
    if not structure.topology:
        structure.topology = activeTopology
 
def _ParseConstrForce(block, structure):

    activeTopology, vectors = _ParseTopologicalBlock(block, structure)

    if structure.force:
        structure.force = np.add( structure.force, np.array( vectors ) );
    else:
        structure.force = np.array( vectors )

    # save topology if not yet there
    if not structure.topology:
        structure.topology = activeTopology

def ParseCnf( ifstream ):
    
    # Parser map
    parseFunctions = dict()
    parseFunctions["TITLE"] = _ParseTitle
    parseFunctions["TIMESTEP"] = _ParseTimeStep
    parseFunctions["POSITION"] = _ParsePosition
    parseFunctions["LATTICESHIFTS"] = _ParseLatticeShifts
    parseFunctions["VELOCITY"] = _ParseVelocity
    parseFunctions["GENBOX"] = _ParseGenbox
    parseFunctions["COSDISPLACEMENTS"] = _ParseCosDiplacements
    parseFunctions["FREEFORCE"] = _ParseFreeForce
    parseFunctions["CONSFORCE"] = _ParseConstrForce    
    
    tokenizer = Tokenizer( ifstream )
    
    # Save blocks that we already found with an increasing index
    # Then we can edit structures later even if they are in a stupid order
    occurances = dict()
    
    # Add a single structure to the map
    structures = []
    
    # preload occurances
    for key in parseFunctions:
        occurances[key] = 0
    
    ## Uses occurance map to be order agnostic
    for blockName, block in tokenizer.Blocks():
        
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseCnf", "Unknown cnf block %s, if is an reduced block please read in a trajectory instead" % (blockName) )
        
        # Fetch the corresponding structure
        structureIndex = occurances[blockName]
        
        while structureIndex >= len(structures):
            structures.append( Structure() )
        
        structure = structures[structureIndex]
        
        # Read data
        parseFunctions[blockName]( block, structure )
        
        # increment occurance
        occurances[blockName] += 1
    
    return structures;        
