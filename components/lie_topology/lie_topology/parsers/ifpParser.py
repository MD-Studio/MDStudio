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
import json
import numpy as np

from lie_topology.common.tokenizer        import Tokenizer
from lie_topology.common.exception        import LieTopologyException
from lie_topology.forcefield.forcefield   import ForceField, MassType, BondType, AngleType

def _ParseTitle(block, forcefield):

    forcefield.description = ' '.join(block)

def _ParseForceField(block, forcefield):

    forcefield.name = block[0]

def _ParseMakeTopVersion(block, forcefield):

    pass

def _ParseMassTypes(block, forcefield):

    nrmaty = int( block[0] )
    nmaty  = int( block[1] )
    
    if len( block ) != nrmaty * 3 + 2:
        
        raise LieTopologyException( "IfpParser::_ReadMassTypes", "Mass types block has incorrect number of arguments!" )
    
    it = 2
    for i in range( 0, nrmaty ):
        
        type_code = block[ it + 0 ]
        mass      = float( block[ it + 1 ] )
        type_name = block[ it + 2 ]
        
        massType = MassType( name=type_code, mass=mass, type_name=type_name )
        forcefield.masstypes.insert( type_code, massType )
            
        it+=3

def _ParseBondTypes(block, forcefield):

    nrbty = int( block[0] )
    bty   = int( block[1] )
    
    if len( block ) != nrbty * 4 + 2:
        
        raise LieTopologyException( "IfpParser::ReadBondType", "Bond types block has incorrect number of arguments!" )

    it = 2
    for i in range( 0, nrbty ):

        bond_type   = block[ it + 0 ]
        fc_quartic  = float( block[ it + 1 ] )
        fc_harmonic = float( block[ it + 2 ] )
        bond0       = float( block[ it + 3 ] )
        
        bond = BondType( name=bond_type, fc_quartic=fc_quartic, fc_harmonic=fc_harmonic, bond0=bond0)
        forcefield.bondtypes.insert( bond_type, bond )

        it+=4

def _ParseAngleTypes(block, forcefield):
           
    nrtty = int( block[0] )
    nrty  = int( block[1] )
    
    if len( block ) != nrtty * 4 + 2:
        
        raise LieTopologyException( "IfpParser::ReadAngleTypes", "Angle types block has incorrect number of arguments!" )
    
    it = 2
    for i in range( 0, nrtty ):
        
        angle_type      = block[ it + 0 ]
        fc_cos_harmonic = float( block[ it + 1 ] )
        fc_harmonic     = float( block[ it + 2 ] )
        angle0          = float( block[ it + 3 ] )
        
        angle = AngleType( name=angle_type, fc_cos_harmonic=fc_cos_harmonic, fc_harmonic=fc_harmonic, angle0=angle0 ) 
        forcefield.angletypes.insert( angle_type,  angle )

        it+=4

def _ParseImproperTypes(block, forcefield):

    nrqty = int( block[0] )
    nqty  = int( block[1] )
    
    if len( block ) != nrqty * 3 + 2:
        
        raise LieTopologyException( "IfpParser::ReadImproperTypes", "Improper types block has incorrect number of arguments!" )
    
    it = 2
    for i in range( 0, nrqty ):
        
        improper_type  = block[ it + 0 ]
        force_constant = float( block[ it + 1 ] )
        angle0         = float( block[ it + 2 ] )
        
        improper = ImproperType(name=improper_type, force_constant=force_constant, angle0=angle0 )
        forcefield.impropertypes.insert( improper_type,  improper )

        it+=3

def _ParseDihedralTypes(block, forcefield):

    nrqty = int( block[0] )
    nqty  = int( block[1] )
    
    if len( block ) != nrqty * 4 + 2:
        
        raise LieTopologyException( "IfpParser::ReadImproperTypes", "Improper types block has incorrect number of arguments!" )
    
    it = 2
    for i in range( 0, nrqty ):
        
        dihedral_type  = block[ it + 0 ]
        force_constant = float( block[ it + 1 ] )
        phaseShift     = float( block[ it + 2 ] )
        multiplicity   = int(   block[ it + 3 ] )
        
        dihedral = DihedralType(name=dihedral_type, force_constant=force_constant, phaseShift=phaseShift, multiplicity=multiplicity)
        forcefield.dihedraltypes.insert( dihedral_type,  dihedral )

        it+=4

def _ParseVdwTypes(block, forcefield):

    nratt = int( block[0] )
        
    if len( block ) != nratt * ( 8 + nratt ) + 1:
        
        raise LieTopologyException( "IfpParser::ReadVdwTypes", "Vdw types block has incorrect number of arguments!" ) 
    
    
    matrix_stack = []

    it = 1
    for i in range( 0, nratt ):
        
        vdw_type = block[ it + 0 ]
        name     = block[ it + 1 ]
        c6       = float( block[ it + 2 ] )
        c12_1    = float( block[ it + 3 ] )
        c12_2    = float( block[ it + 4 ] )
        c12_3    = float( block[ it + 5 ] )
        c6_14    = float( block[ it + 6 ] )
        c12_14   = float( block[ it + 7 ] )
        
        it+=8
        
        vdw_type = VdwType( name=vdw_type, type_name=name, c6=c6, c6_14=c6_14,\
                            c12=[c12_1, c12_2, c12_3], c12_14=c12_14  )

        forcefield.vdwtypes.insert( vdw_type,  vdw_type )

        #now read in the matrix
        matrix = []
        for j in range( 0, nratt ):
            
            matEntry = int( tokenStream[ it  ] )
            matrix.append(matEntry)

            # 
            it+=1
        
        # we postpone matrix handling till we read all types
        matrix_stack.append(matrix)
        
        
    # start resolving matrix entries
    for i in range( 0, nratt ):

        vdw_type = forcefield.vdwtypes.at(i)
        vdw_type.matrix = dict()

        for j in range( 0, nratt ):

            matEntry = matrix_stack[i][j]
            target_type = forcefield.vdwtypes.keyAt(j)

            if matEntry > 1:
                vdw_type.matrix[target_type] = matEntry

def _ParseVdwMixed(block, forcefield):

    nrpr = int( len(tokenStream) / 6 )
        
    if len( tokenStream ) % 6 != 0:
        
        raise PygromosException( "IfpParser::ReadVdwMixed", "Vdw mixed block has incorrect number of arguments!" ) 
    
    it = 0
    for i in range( 0, nrpr ):
        
        ref1 = int( tokenStream[ it + 0 ] )
        ref2 = int( tokenStream[ it + 1 ] )	
        
        c6     = float( tokenStream[ it + 2 ] )
        c12    = float( tokenStream[ it + 3 ] )
        c6_14  = float( tokenStream[ it + 4 ] )
        c12_14 = float( tokenStream[ it + 5 ] )
        
        ref1_name = forcefield.vdwtypes.keyAt(ref1)
        ref2_name = forcefield.vdwtypes.keyAt(ref2)

        mixed = VdwMixed( references=[ref1_name,ref2_name], c6=c6, c12=c12, c6_14=c6_14, c12_14=c12_14 )
        type_name = "%s::%s" % ( ref1_name, ref2_name )
        forcefield.vdwmixed.Insert( type_name, mixed ) 

        it += 6

def ParseIfp( ifstream ):

    # Parser map
    parseFunctions = dict()
    parseFunctions["TITLE"]                 = _ParseTitle
    parseFunctions["FORCEFIELD"]            = _ParseForceField
    parseFunctions["MAKETOPVERSION"]        = _ParseMakeTopVersion
    parseFunctions["MASSATOMTYPECODE"]      = _ParseMassTypes
    parseFunctions["BONDSTRETCHTYPECODE"]   = _ParseBondTypes
    parseFunctions["BONDANGLEBENDTYPECODE"] = _ParseAngleTypes
    parseFunctions["IMPDIHEDRALTYPECODE"]   = _ParseImproperTypes
    parseFunctions["TORSDIHEDRALTYPECODE"]  = _ParseDihedralTypes
    parseFunctions["SINGLEATOMLJPAIR"]      = _ParseVdwTypes
    parseFunctions["MIXEDATOMLJPAIR"]       = _ParseVdwMixed

    tokenizer = Tokenizer( ifstream )

    forcefield = ForceField()

    for blockName, block in tokenizer.Blocks():
        
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseIfp", "Unknown ifp block %s" % (blockName) )
        
        # Read data
        parseFunctions[blockName]( block, forcefield )
        
    return forcefield