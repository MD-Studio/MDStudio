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

from lie_topology.common.pbc import RectBox
from lie_topology.common.tokenizer import Tokenizer;
from lie_topology.common.exception import PygromosException;

def _ParseCnfPositions( stream ):
    
    pass;


def ParseCnf( path, moleculeHandle, solventHandle ):
        
    atoms = [];
    
    tokenizer = Tokenizer( structurefile );
    stream = tokenizer.GetStream();
    
    if not "POSITION" in stream:
        
        raise PygromosException( "CnfControl::_ParseCnf", "Expected an POSITION block in the cnf stream!" );
    
    if not "GENBOX" in stream:
        
        raise PygromosException( "CnfControl::_ParseCnf", "Expected an GENBOX block in the cnf stream!" );
    
    positions = stream["POSITION"][0];
   
    for resNum, resName, atomName, atomNum, x, y, z in zip(positions[0::7], positions[1::7], positions[2::7], positions[3::7], positions[4::7], positions[5::7], positions[6::7]):	
        
        atoms.append( CnfControl.Atom( atomNum, atomName, resName, resNum, ( float(x), float(y), float(z) ) ) );
    
    
    box = stream["GENBOX"][0];
    
    if int(box[0]) != 1:
        
        raise PygromosException( "CnfControl::_ParseCnf", "Tried to read in an box type that is not rectangular, this is currently not supported!" );
    
    self.box = RectBox( float( box[1] ), float( box[2] ), float( box[3] ) );
    
    #
    # Set ranges
    # 
    self.soluteStart = 0;
    self.soluteEnd = moleculeHandle.solute.atoms.Size();
    self.solventStart = self.soluteEnd;
    self.solventEnd = len( atoms );
    self.numSolventMol = ( self.solventEnd - self.solventStart ) / solventHandle.solute.atoms.Size();
    
    for i in range( self.soluteStart, self.soluteEnd ):
        
        if atoms[i].residueName != moleculeHandle.meta.name:
            
            raise PygromosException( "CnfControl::_ParseCnf", "Solute residue %s does not match the solute name %s in the template!" % ( atoms[i].residueName, moleculeHandle.meta.name ) );
        
        if atoms[i].atomName != moleculeHandle.solute.atoms.KeyAt( i ):
            
            raise PygromosException( "CnfControl::_ParseCnf", "Solute atom %s does not match the solute name %s in the template!" % ( atoms[i].atomName, moleculeHandle.solute.atoms.KeyAt( i ) ) );
        
        self.coords.append( atoms[i].coords );
        
    for i in range ( self.solventStart, self.solventEnd ):
        
        solvAtomIndex = ( i - self.solventStart ) % solventHandle.solute.atoms.Size();
        
        # we allow SOLV as another option
        if atoms[i].residueName != solventHandle.meta.name and atoms[i].residueName != "SOLV":
            
            raise PygromosException( "CnfControl::_ParseCnf", "Solvent residue %s does not match the solute name %s in the template!" % ( atoms[i].residueName, solventHandle.meta.name ) );
        
        if atoms[i].atomName != solventHandle.solute.atoms.KeyAt( solvAtomIndex ):
            
            raise PygromosException( "CnfControl::_ParseCnf", "Solvent atom %s does not match the solute name %s in the template!" % ( atoms[i].atomName, solventHandle.solute.atoms.KeyAt( solvAtomIndex ) ) ); 
        
        self.coords.append( atoms[i].coords );
