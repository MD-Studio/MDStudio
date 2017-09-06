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

from lie_topology.common.tokenizer          import Tokenizer
from lie_topology.common.exception          import LieTopologyException
from lie_topology.molecule.molecule         import Molecule
from lie_topology.molecule.bond             import Bond
from lie_topology.molecule.angle            import Angle
from lie_topology.molecule.dihedral         import Dihedral
from lie_topology.molecule.improper         import Improper
from lie_topology.molecule.vsite            import InPlaneSite
from lie_topology.molecule.reference        import AtomReference

def _GenAatopRef( solute, index ):

    ref = None

    # if not within index boundaries, its an external ref
    if index >= 0 and index < len(solute.atoms):
        ref = solute.atoms.at( index ).key
    
    else:
        ref = "REPLACE_%i" % (index)

    return ref

def _ParseSoluteBonds( block, solute, it ):

    numBonds = int( block[it] ) 
    it+=1

    print ("    bonds:")

    for i in range ( 0, numBonds ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1

        atom_i_ref = _GenAatopRef( solute, index_i )
        atom_j_ref = _GenAatopRef( solute, index_j )

        print ("      - indices: [ %s, %s ]" % ( atom_i_ref, atom_j_ref ))
        print ("        type: gb_%s" % (block[it+2]))
        
        it+=3
    
    return it

def _ParseSoluteAngles( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    print ("    angles:")

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1

        atom_i_ref = _GenAatopRef( solute, index_i )
        atom_j_ref = _GenAatopRef( solute, index_j )
        atom_k_ref = _GenAatopRef( solute, index_k )

        print ("      - indices: [ %s, %s, %s ]" % ( atom_i_ref, atom_j_ref, atom_k_ref ))
        print ("        type: ga_%s" % (block[it+3]))
        
        it+=4
    
    return it

def _ParseSoluteDihedrals( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    print ("    dihedrals:")

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1
        index_l = int( block[it+3] ) - 1

        atom_i_ref = _GenAatopRef( solute, index_i )
        atom_j_ref = _GenAatopRef( solute, index_j )
        atom_k_ref = _GenAatopRef( solute, index_k )
        atom_l_ref = _GenAatopRef( solute, index_l )

        print ("      - indices: [ %s, %s, %s, %s ]" % ( atom_i_ref, atom_j_ref, atom_k_ref, atom_l_ref ))
        print ("        type: gd_%s" % (block[it+4]))
        
        it+=5
    
    return it

def _ParseSoluteImpropers( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    print ("    impropers:")

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1
        index_l = int( block[it+3] ) - 1
        
        atom_i_ref = _GenAatopRef( solute, index_i )
        atom_j_ref = _GenAatopRef( solute, index_j )
        atom_k_ref = _GenAatopRef( solute, index_k )
        atom_l_ref = _GenAatopRef( solute, index_l )

        print ("      - indices: [ %s, %s, %s, %s ]" % ( atom_i_ref, atom_j_ref, atom_k_ref, atom_l_ref ))
        print ("        type: gi_%s" % (block[it+4]))
        
        it+=5
    
    return it

def _ParsePrecedingExclusions( block, solute, count, it ):

    ## We totally ignore exclusions right now
    ## They are generated on the fly

    for excluIndex in range ( 0, count ):

        index = block[it + 0]
        numNeighbours = int( block[it + 1] )

        it += 2
        
        #ignore
        it += numNeighbours
            
    return it

map_54A7_vdw = [
    "O", "OM", "OA", "OE", "OW", "N", "NT", "NL", "NR", "NZ", "NE", "C", "CH0", "CH1", "CH2",   
    "CH3", "CH4", "CH2r", "CR1", "HC", "H", "DUM", "S", "CU1+", "CU2+", "FE", "ZN2+",
    "MG2+", "CA2+", "P", "AR", "F", "CL", "BR", "CMet", "OMet", "NA+", "CL-", "CChl",
    "CLChl", "HChl", "SDmso", "CDmso", "ODmso", "CCl4", "CLCl4", "FTFE",
    "CTFE", "CHTFE", "OTFE", "CUrea", "OUrea", "NUrea", "CH3p" ]

map_54A7_mass = {
    1: "H",    3: "CH1", 4: "CH2", 5: "CH3",
    6: "CH4", 12: "C",  14: "N",  16: "O",
   19: "F",   23: "NA", 24: "MG",  28: "SI",
   31: "P",   32: "S",  35: "CL",  39: "AR",
   40: "CA",  56: "FE", 63: "CU",  65: "ZN",
   80: "BR"
}

def _ParseSoluteAtoms( block, solute, count, it, trailing, cgIndex ):

    for atom in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int( block[it + 0] )  - 1
        name           = block[it + 1]
        vdwGroup       = int( block[it + 2] ) - 1
        massGroup      = int( block[it + 3] )
        charge         = block[it + 4]
        chargeGroup_fl = int( block[it + 5] )
        
        solute.AddAtom( key=name, type_name=name, identifier=index )
        atom = solute.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        #atom.mass_type = ForceFieldReference( key=massGroup )
        #atom.vdw_type  = ForceFieldReference( key=vdwGroup )
        
        # These are define here on the spot
        #atom.coulombic_type = CoulombicType( charge=charge )
        #atom.charge_group   = cgIndex
      
        print ("      %s:" % (name) )
        print ("        vdw-type: %s" % (map_54A7_vdw[vdwGroup]) )
        print ("        mass-type: %s" % ( map_54A7_mass[massGroup] ) )
        print ("        charge: %s" % (charge) )
        print ("        charge-type: null" )
        print ("        charge-group: %i" % (cgIndex) )
        
        if not trailing:
            # parse number of exclusions
            numNeighbours = int( block[it + 6] )

            # then add the numbers of neighbours + 1 for the
            # count location
            it += numNeighbours + 1
    
        it += 6

        if chargeGroup_fl == 1:
            cgIndex += 1

    return it, cgIndex

def _ParseAtomicData( block, solute, it):

    numAtoms = int( block[it+0] )
    numExclu = int( block[it+1] )
    cgIndex = 0
    print ("    atoms:")

    # Handle preceding exclusions
    it = _ParsePrecedingExclusions( block, solute, numExclu, it+2 )

    # Parse full atom description
    it, cgIndex = _ParseSoluteAtoms( block, solute, numAtoms - numExclu, it, False, cgIndex )

    # Parse trailing atoms in ( for chains )
    it, cgIndex = _ParseSoluteAtoms( block, solute, numExclu, it, True, cgIndex )

    return it

def _ParseBondedData(block, solute, it ):

    # Parse bond data
    it = _ParseSoluteBonds( block, solute, it )

    # Parse angle data
    it = _ParseSoluteAngles( block, solute, it )

    # Parse improper data
    it = _ParseSoluteImpropers( block, solute, it )

    # Parse dihedral data
    it = _ParseSoluteDihedrals( block, solute, it )

    return it

def _ParseSoluteBuildingBlock(block):

    print ("  %s:" % (block[0]) )
    print ("    variants:")
    print ("      NH3+_%s: NH3+" % (block[0]) )
    print ("      %s_COO-: COO-" % (block[0]) )

    solute = Molecule( key=block[0], type_name=block[0] )

    it = _ParseAtomicData( block, solute, 1 )
    it = _ParseBondedData( block, solute, it )

def _Void(block):

    pass

def ConvMtb( ifstream ):

    # Parser map
    parseFunctions = dict()
    parseFunctions["TITLE"]               = _Void
    parseFunctions["FORCEFIELD"]          = _Void
    parseFunctions["MAKETOPVERSION"]      = _Void
    parseFunctions["PHYSICALCONSTANTS"]   = _Void
    parseFunctions["LINKEXCLUSIONS"]      = _Void
    parseFunctions["MTBUILDBLSOLUTE"]     = _ParseSoluteBuildingBlock
    parseFunctions["MTBUILDBLPOLSOLUTE"]  = _Void
    parseFunctions["MTBUILDBLSOLVENT"]    = _Void
    parseFunctions["MTBUILDBLPOLSOLVENT"] = _Void
    parseFunctions["MTBUILDBLEND"]        = _Void

    tokenizer = Tokenizer( ifstream )

    ## Uses occurance map to be order agnostic
    for blockName, block in tokenizer.Blocks():
        
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseMtb", "Unknown mtb block %s" % (blockName) )
        
        # Read data
        parseFunctions[blockName]( block )
        
if __name__ == '__main__':

    with open(sys.argv[1]) as ifs:

        ConvMtb(ifs)