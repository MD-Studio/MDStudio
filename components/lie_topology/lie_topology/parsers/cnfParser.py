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

from copy import deepcopy

from lie_topology.common.tokenizer import Tokenizer;
from lie_topology.common.exception import LieTopologyException;
from lie_topology.molecule.structure import Structure

def _ParseTitle(block, structure):

    #currently not used
    pass;


def _ParseTimeStep(block, structure):

    #currently not used
    pass;

def _ParsePosition(block, structure):
    
    activeTopology = None
    activeResNum = None
    
    if not structure.topology:
        
        # Start parsing a topology this round
        activeTopology =
        
    # If the structure does not have a topology yet
    for resNum, resName, atomName, atomNum, x, y, z in zip(block[0::7], block[1::7], 
                                                           block[2::7], block[3::7], 
                                                           block[4::7], block[5::7], 
                                                           block[6::7]):	
        
        print (resName)
        
        #atoms.append( CnfControl.Atom( atomNum, atomName, resName, resNum, ( float(x), float(y), float(z) ) ) );

    #currently not used
    pass;

def _ParseLatticeShifts(block, structure):

    #currently not used
    pass;
    
def _ParseVelocity(block, structure):

    #currently not used
    pass;
    
def _ParseGenbox(block, structure):

    #currently not used
    pass;

def _ParseCosDiplacements(block, structure):

    #currently not used
    pass;

def _ParseFreeForce(block, structure):

    #currently not used
    pass;
 
def _ParseConstrForce(block, structure):

    #currently not used
    pass; 

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
    occurances = dict();
    
    # Add a single structure to the map
    structures = [ Structure() ];
    
    # preload occurances
    for key in parseFunctions:
        occurances[key] = 0;
    
    ## Uses occurance map to be order agnostic
    for blockName, block in tokenizer.Blocks():
    
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseCnf", "Unknown cnf block %s, if is an reduced block please read in a trajectory instead" % (blockName) )
        
        # Fetch the corresponding structure
        structureIndex = occurances[blockName]
        
        while structureIndex >= len(structures):
            structures.append( Structure() )
        
        structure = structures[structureIndex];
        
        # Read data
        parseFunctions[blockName]( block, structure );
        
    
        # increment occurance
        occurances[blockName] += 1;
    
    return structures;        
