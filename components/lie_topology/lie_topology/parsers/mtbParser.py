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
from lie_topology.filetypes.buildingBlock import BuildingBlock
from lie_topology.molecule.molecule       import Molecule
from lie_topology.molecule.bond           import Bond
from lie_topology.molecule.angle          import Angle
from lie_topology.molecule.dihedral       import Dihedral
from lie_topology.molecule.vsite          import InPlaneSite
from lie_topology.forcefield.forcefield   import CoulombicType
from lie_topology.forcefield.reference    import ForceFieldReference

def _ParseTitle(block, mtb_file):

    mtb_file.title = ' '.join(block)

def _ParseForcefield(block, mtb_file):

    pass

def _ParseLinkExcl(block, mtb_file):

    mtb_file.exclusion_distance = int( block[0] )

def _ParsePhysConst(block, mtb_file):

    mtb_file.physical_constants.four_pi_eps0_i     = float( block[0] )
    mtb_file.physical_constants.plancks_constant   = float( block[1] )
    mtb_file.physical_constants.speed_of_light     = float( block[2] )
    mtb_file.physical_constants.boltzmann_constant = float( block[3] )

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

def _ParseSoluteBonds( block, solute, it ):

    numBonds = int( block[it] ) 
    it+=1

    for i in range ( 0, numBonds ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        bond_type = ForceFieldReference( block[it+2] )

        atom_i_name = solute.atoms.keyAt( index_i )
        atom_j_name = solute.atoms.keyAt( index_j )
        
        bond = Bond( atom_names=[atom_i_name,atom_j_name],\
                     bond_type=bond_type  ) 

        solute.bonds.append( bond )
        
        it+=3
    
    return it

def _ParseSoluteAngles( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1
        angle_type = ForceFieldReference( block[it+3] )

        atom_i_name = solute.atoms.keyAt( index_i )
        atom_j_name = solute.atoms.keyAt( index_j )
        atom_k_name = solute.atoms.keyAt( index_k )

        angle = Angle( atom_names=[atom_i_name,atom_j_name, atom_k_name],\
                       angle_type=angle_type  ) 

        solute.angles.append( angle )
        
        it+=4
    
    return it

def _ParseSoluteDihedrals( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1
        index_l = int( block[it+3] ) - 1
        dihedral_type = ForceFieldReference( block[it+4] )

        atom_i_name = solute.atoms.keyAt( index_i )
        atom_j_name = solute.atoms.keyAt( index_j )
        atom_k_name = solute.atoms.keyAt( index_k )
        atom_l_name = solute.atoms.keyAt( index_k )

        dihedral = Dihedral( atom_names=[atom_i_name,atom_j_name, atom_k_name, atom_l_name],\
                             dihedral_type=dihedral_type  ) 

        solute.dihedrals.append( dihedral )
        
        it+=5
    
    return it

def _ParseSoluteImpropers( block, solute, it ):

    numAngles = int( block[it] ) 
    it+=1

    for i in range ( 0, numAngles ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        index_k = int( block[it+2] ) - 1
        index_l = int( block[it+3] ) - 1
        dihedral_type = ForceFieldReference( block[it+4] )

        atom_i_name = solute.atoms.keyAt( index_i )
        atom_j_name = solute.atoms.keyAt( index_j )
        atom_k_name = solute.atoms.keyAt( index_k )
        atom_l_name = solute.atoms.keyAt( index_k )

        dihedral = Dihedral( atom_names=[atom_i_name,atom_j_name, atom_k_name, atom_l_name],\
                             dihedral_type=dihedral_type  ) 

        solute.impropers.append( dihedral )
        
        it+=5
    
    return it

def _ParseSoluteAtoms( block, solute, count, it, exclusions ):

    cgIndex = 0

    for atom in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int( block[it + 0] )  - 1
        name           = block[it + 1]
        vdwGroup       = block[it + 2]
        massGroup      = block[it + 3]
        charge         = block[it + 4]
        chargeGroup_fl = int( block[it + 5] )
        numNeighbours  = int( block[it + 6] )
        
        if chargeGroup_fl == 1:
            cgIndex += 1

        solute.AddAtom( name=name, identifier=index )
        atom = solute.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        atom.mass_type = ForceFieldReference( name=massGroup )
        atom.vdw_type  = ForceFieldReference( name=vdwGroup )
        
        # These are define here on the spot
        atom.coulombic_type = CoulombicType( charge=charge )
        atom.charge_group   = cgIndex
      
        it += 7

        if exclusions:
            it += numNeighbours
    
    return it

def _ParseAtomicPolarizabilities(block, solute, it ):

    count = int( block[it] )
    it+=1

    for i in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int(   block[it + 0] ) - 1
        polarizability = float( block[it + 0] )
        cos_charge     = float( block[it + 0] )  
        damping_level  = float( block[it + 0] )  
        damping_power  = float( block[it + 0] )  
        gamma          = float( block[it + 0] )  
        offset_i       = int(   block[it + 0] ) - 1
        offset_j       = int(   block[it + 0] ) - 1
         
        atom_name, atom = solute.atoms.at( index )

        atom.coulombic_type.polarizability = polarizability
        atom.coulombic_type.cos_charge     = cos_charge
        atom.coulombic_type.damping_level  = damping_level
        atom.coulombic_type.damping_power  = damping_power

        if gamma != 0.0:

            atom_i_name = solute.atoms.keyAt( offset_i )
            atom_j_name = solute.atoms.keyAt( offset_j )

            atom.vsite = InPlaneSite( atom_names=[atom_i_name,atom_j_name], gamma=gamma )
            

        it += 8

    return it

def _ParseAtomicData( block, solute, it ):

    numAtoms = int( block[it+0] )
    numExclu = int( block[it+1] )

    # Handle preceding exclusions
    it = _ParsePrecedingExclusions( block, solute, numExclu, it+2 )

    # Parse full atom description
    it = _ParseSoluteAtoms( block, solute, numAtoms - numExclu, it, True )

    # Parse trailing atoms in ( for chains )
    it = _ParseSoluteAtoms( block, solute, numExclu, it, False )

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

def _ParsePolarizableSoluteBuildingBlock(block, mtb_file):

    solute = Molecule()
    solute.name = block[0]

    it = _ParseAtomicData( block, solute, 1 )
    it = _ParseAtomicPolarizabilities(block, solute, it )
    it = _ParseBondedData( block, solute, it )
    
    numVdwExceptions = int( tokenStream[it] )
    if ( numVdwExceptions > 0 ):
        raise PygromosException( "_ParsePolarizableSoluteBuildingBlock", "MTB van der Waals exceptions not supported" )

def _ParseSoluteBuildingBlock(block, mtb_file):

    solute = Molecule()
    solute.name = block[0]

    it = _ParseAtomicData( block, solute, 1 )
    it = _ParseBondedData( block, solute, it )
    
    numVdwExceptions = int( block[it] )
    if ( numVdwExceptions > 0 ):
        raise PygromosException( "_ParseSoluteBuildingBlock", "MTB van der Waals exceptions not supported" )

    print json.dumps( solute.OnSerialize(), indent=2 )

def ParseMtb( ifstream ):

    # Parser map
    parseFunctions = dict()
    parseFunctions["TITLE"] = _ParseTitle
    parseFunctions["FORCEFIELD"] = _ParseForcefield
    parseFunctions["PHYSICALCONSTANTS"] = _ParsePhysConst
    parseFunctions["LINKEXCLUSIONS"] = _ParseLinkExcl
    parseFunctions["MTBUILDBLSOLUTE"] = _ParseSoluteBuildingBlock

    tokenizer = Tokenizer( ifstream )

    mtb_file = BuildingBlock()

    ## Uses occurance map to be order agnostic
    for blockName, block in tokenizer.Blocks():
        
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseMtb", "Unknown mtb block %s" % (blockName) )
        
        # Read data
        parseFunctions[blockName]( block, mtb_file )
        
    return mtb_file