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
from lie_topology.molecule.blueprint        import Blueprint
from lie_topology.molecule.molecule         import Molecule
from lie_topology.molecule.bond             import Bond
from lie_topology.molecule.angle            import Angle
from lie_topology.molecule.dihedral         import Dihedral
from lie_topology.molecule.vsite            import InPlaneSite
from lie_topology.molecule.reference        import AtomReference
from lie_topology.forcefield.forcefield     import CoulombicType, BondType
from lie_topology.forcefield.reference      import ForceFieldReference

def _ParseTitle(block, mtb_file):

    mtb_file.title = ' '.join(block)

def _ParseVersion(block, mtb_file):

    pass

def _ParseForcefield(block, mtb_file):

    pass

def _GenerateBondedReference( solute, index ):

    ref = None

    # if not within index boundaries, its an external ref
    if index >= 0 and index < len(solute.atoms):
        ref = solute.atoms.at( index )
    
    else:
        ref = AtomReference(external_index=index)

    return ref

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
        
        atom_i_ref = _GenerateBondedReference( solute, index_i )
        atom_j_ref = _GenerateBondedReference( solute, index_j )
        
        bond = Bond( atom_references=[atom_i_ref,atom_j_ref],\
                     bond_type=bond_type  ) 

        solute.AddBond( bond )
        
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

        atom_i_ref = _GenerateBondedReference( solute, index_i )
        atom_j_ref = _GenerateBondedReference( solute, index_j )
        atom_k_ref = _GenerateBondedReference( solute, index_k )

        angle = Angle( atom_references=[atom_i_ref,atom_j_ref, atom_k_ref],\
                       angle_type=angle_type  ) 

        solute.AddAngle( angle )
        
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

        atom_i_ref = _GenerateBondedReference( solute, index_i )
        atom_j_ref = _GenerateBondedReference( solute, index_j )
        atom_k_ref = _GenerateBondedReference( solute, index_k )
        atom_l_name = _GenerateBondedReference( solute, index_k )

        dihedral = Dihedral( atom_references=[atom_i_ref,atom_j_ref, atom_k_ref, atom_l_name],\
                             dihedral_type=dihedral_type  ) 

        solute.AddDihedral( dihedral )
        
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

        atom_i_ref = _GenerateBondedReference( solute, index_i )
        atom_j_ref = _GenerateBondedReference( solute, index_j )
        atom_k_ref = _GenerateBondedReference( solute, index_k )
        atom_l_name = _GenerateBondedReference( solute, index_k )

        dihedral = Dihedral( atom_references=[atom_i_ref,atom_j_ref, atom_k_ref, atom_l_name],\
                             dihedral_type=dihedral_type  ) 

        solute.AddImproper( dihedral )
        
        it+=5
    
    return it

def _ParseSoluteAtoms( block, solute, count, it, trailing ):

    cgIndex = 0

    for atom in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int( block[it + 0] )  - 1
        name           = block[it + 1]
        vdwGroup       = block[it + 2]
        massGroup      = block[it + 3]
        charge         = block[it + 4]
        chargeGroup_fl = int( block[it + 5] )
        
        if chargeGroup_fl == 1:
            cgIndex += 1

        solute.AddAtom( key=name, type_name=name, identifier=index, trailing=trailing )
        atom = solute.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        atom.mass_type = ForceFieldReference( key=massGroup )
        atom.vdw_type  = ForceFieldReference( key=vdwGroup )
        
        # These are define here on the spot
        atom.coulombic_type = CoulombicType( charge=charge )
        atom.charge_group   = cgIndex
      
        if not trailing:
            # parse number of exclusions
            numNeighbours = int( block[it + 6] )

            # then add the numbers of neighbours + 1 for the
            # count location
            it += numNeighbours + 1
    
        it += 6

    return it

def _ParseAtomicPolarizabilities(block, solute, it):

    count = int( block[it] )
    it+=1

    for i in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int(   block[it + 0] ) - 1
        polarizability = float( block[it + 1] )
        cos_charge     = float( block[it + 2] )  
        damping_level  = float( block[it + 3] )  
        damping_power  = float( block[it + 4] )  
        gamma          = float( block[it + 5] )  
        offset_i       = int(   block[it + 6] ) - 1
        offset_j       = int(   block[it + 7] ) - 1
         
        atom_name, atom = solute.atoms.at( index )

        atom.coulombic_type.polarizability = polarizability
        atom.coulombic_type.cos_charge     = cos_charge
        atom.coulombic_type.damping_level  = damping_level
        atom.coulombic_type.damping_power  = damping_power

        if gamma != 0.0:

            atom_i_ref = _GenerateBondedReference( solute, offset_i )
            atom_j_ref = _GenerateBondedReference( solute, offset_j )

            atom.vsite = InPlaneSite( atom_references=[atom_i_ref,atom_j_ref], gamma=gamma )
            
        it += 8

    return it

def _ParseSolventAtoms(block, solvent, it):

    count = int( block[it] )
    it+=1

    for atom in range ( 0, count ):
        
        # Minus one as gromos uses fortran indices
        index          = int( block[it + 0] )  - 1
        name           = block[it + 1]
        vdwGroup       = block[it + 2]
        massGroup      = block[it + 3]
        charge         = block[it + 4]

        solvent.AddAtom( key=name, type_name=name, identifier=index )
        atom = solvent.atoms.back()
        
        # These parameters are externally defined
        # Therefore we can only reference to them at this point
        atom.mass_type = ForceFieldReference( key=massGroup )
        atom.vdw_type  = ForceFieldReference( key=vdwGroup )
        
        # These are define here on the spot
        atom.coulombic_type = CoulombicType( charge=charge )

        it += 5

    return it

def _ParseSolventConstraints(block, solvent, it):

    numConstr = int( block[it] ) 
    it+=1

    if solvent.bonds is None:
        solvent.bonds = []

    for i in range ( 0, numConstr ):

        # Minus one as gromos uses fortran indices
        index_i = int( block[it+0] ) - 1
        index_j = int( block[it+1] ) - 1
        bond_length = float( block[it+2] )
        
        atom_i_ref = _GenerateBondedReference( solvent, index_i )
        atom_j_ref = _GenerateBondedReference( solvent, index_j )
        
        bond_type = BondType( bond0 = bond_length )
        bond = Bond( atom_references=[atom_i_ref,atom_j_ref],\
                     bond_type=bond_type  ) 

        solvent.bonds.append( bond )
        
        it+=3
    
    return it

def _ParseAtomicData( block, solute, it):

    numAtoms = int( block[it+0] )
    numExclu = int( block[it+1] )

    # Handle preceding exclusions
    it = _ParsePrecedingExclusions( block, solute, numExclu, it+2 )

    # Parse full atom description
    it = _ParseSoluteAtoms( block, solute, numAtoms - numExclu, it, False )

    # Parse trailing atoms in ( for chains )
    it = _ParseSoluteAtoms( block, solute, numExclu, it, True )

    return it

def _ParseBlendData( block, solute, it ):

    numAtoms   = int( block[it+0] )
    numReplace = int( block[it+1] )

    # Parse full atom description
    numFullAtoms = numAtoms - max( 0, numReplace)
    it = _ParseSoluteAtoms( block, solute, numFullAtoms, it+2, False )

    # Parse trailing atoms in ( for chains )
    if numReplace > 0:
        it = _ParseSoluteAtoms( block, solute, numReplace, it, True )
    else:
        # insert preceding atoms to signal ones to delete
        for i in range(0,abs(numReplace)):
            solute.AddAtom( key="-%i"%(i), preceding=True )


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

    solute = Molecule( key=block[0], type_name=block[0] )

    it = _ParseAtomicData( block, solute, 1 )
    it = _ParseAtomicPolarizabilities(block, solute, it )
    it = _ParseBondedData( block, solute, it )
    
    numVdwExceptions = int( tokenStream[it] )
    if ( numVdwExceptions > 0 ):
        raise PygromosException( "_ParsePolarizableSoluteBuildingBlock", "MTB van der Waals exceptions not supported" )

    mtb_file.AddMolecule(molecule=solute)

def _ParseSoluteBuildingBlock(block, mtb_file):

    solute = Molecule( key=block[0], type_name=block[0] )

    it = _ParseAtomicData( block, solute, 1 )
    it = _ParseBondedData( block, solute, it )
    
    numVdwExceptions = int( block[it] )
    if ( numVdwExceptions > 0 ):
        raise PygromosException( "_ParseSoluteBuildingBlock", "MTB van der Waals exceptions not supported" )

    mtb_file.AddMolecule(molecule=solute)

def _ParseBlendBuildingBlock(block, mtb_file):

    solute = Molecule( key=block[0], type_name=block[0] )
    
    it = _ParseBlendData( block, solute, 1 )
    it = _ParseBondedData( block, solute, it )
    
    # blends and molecule are different lists
    # but we still have to check for name collisions
    if mtb_file.FindMolecule( solute.key ) != None:
        raise PygromosException( "_ParseSoluteBuildingBlock", "Blend name %s already present as molecule name" %(solute.key) )

    mtb_file.AddBlend(molecule=solute)

def _ParseSolventBuildingBlock(block, mtb_file):

    solvent = Molecule(key=block[0], type_name=block[0])

    it = _ParseSolventAtoms( block, solvent, 1 )
    it = _ParseSolventConstraints( block, solvent, it )
    
    mtb_file.AddSolvent(molecule=solvent)

def _ParsePolarizableSolventBuildingBlock(block, mtb_file):

    solvent = Molecule(key=block[0], type_name=block[0])

    it = _ParseSolventAtoms( block, solvent, 1 )
    it = _ParseAtomicPolarizabilities(block, solute, it )
    it = _ParseSolventConstraints( block, solvent, it )
    
    numVdwExceptions = int( block[it] )
    if ( numVdwExceptions > 0 ):
        raise PygromosException( "_ParsePolarizableSolventBuildingBlock", "MTB van der Waals exceptions not supported" )

    mtb_file.AddSolvent(molecule=solvent)

def ParseMtb( ifstream ):

    # Parser map
    parseFunctions = dict()
    parseFunctions["TITLE"]               = _ParseTitle
    parseFunctions["FORCEFIELD"]          = _ParseForcefield
    parseFunctions["MAKETOPVERSION"]      = _ParseVersion
    parseFunctions["PHYSICALCONSTANTS"]   = _ParsePhysConst
    parseFunctions["LINKEXCLUSIONS"]      = _ParseLinkExcl
    parseFunctions["MTBUILDBLSOLUTE"]     = _ParseSoluteBuildingBlock
    parseFunctions["MTBUILDBLPOLSOLUTE"]  = _ParsePolarizableSoluteBuildingBlock
    parseFunctions["MTBUILDBLSOLVENT"]    = _ParseSolventBuildingBlock
    parseFunctions["MTBUILDBLPOLSOLVENT"] = _ParsePolarizableSolventBuildingBlock
    parseFunctions["MTBUILDBLEND"]        = _ParseBlendBuildingBlock

    tokenizer = Tokenizer( ifstream )

    mtb_file = Blueprint()
    
    ## Uses occurance map to be order agnostic
    for blockName, block in tokenizer.Blocks():
        
        if not blockName in parseFunctions:
            
            raise LieTopologyException("ParseMtb", "Unknown mtb block %s" % (blockName) )
        
        # Read data
        parseFunctions[blockName]( block, mtb_file )
        
    return mtb_file