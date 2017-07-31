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


from lie_topology.common.serializable import Serializable
from lie_topology.common.exception import LieTopologyException
from lie_topology.common.contiguousMap import ContiguousMap

class CoulombicType( Serializable ):
    
    def __init__( self, key = None, charge = None, polarizability = None, cos_charge = None,\
                  damping_level = None, damping_power = None  ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the charge type
        self.key = key

        # coulombic charge of this type
        self.charge = charge

        # isotropic atomic polarizability
        self.polarizability = polarizability

        # charge on the cos particle
        self.cos_charge = cos_charge

        # damping level
        self.damping_level = damping_level

        # damping power
        self.damping_power = damping_power


class VdwType( Serializable ):
    
    def __init__( self, key = None, type_name = None, c6_sqrt = None, c6_14_sqrt = None, c12_sqrt = None, c12_14_sqrt = None, matrix = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        # specific type name as name could be anything
        self.type_name = type_name

        self.c6_sqrt     = c6_sqrt

        self.c6_14_sqrt  = c6_14_sqrt

        self.c12_sqrt    = c12_sqrt

        self.c12_14_sqrt = c12_14_sqrt

        self.matrix = matrix
        
class VdwMixed( Serializable ):
    
    def __init__( self, references = None, c6 = None, c6_14 = None, c12 = None, c12_14 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        self.references = references

        self.c6     = c6

        self.c6_14  = c6_14

        self.c12    = c12
        
        self.c12_14 = c12_14

class VdwSpecAtom( Serializable ):

    def __init__( self, index = None, c6 = None, c12 = None ):

        self.index = index 

        self.c6     = c6

        self.c12    = c12
        

class MassType( Serializable ):
    
    def __init__( self, key = None, mass = None, type_name = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        # mass of the type
        self.mass = mass

        # explicit name of the type, as name can be anything
        self.type_name = type_name
      
class BondType( Serializable ):
    
    def __init__( self, key = None, fc_quartic = None, fc_harmonic = None, bond0 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        self.fc_quartic = fc_quartic

        self.fc_harmonic = fc_harmonic

        self.bond0 = bond0
    
        
class AngleType( Serializable ):
    
    def __init__( self, key = None, fc_cos_harmonic = None, fc_harmonic = None, angle0 = None  ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        self.fc_cos_harmonic = fc_cos_harmonic

        self.fc_harmonic = fc_harmonic

        self.angle0 = angle0
    

class DihedralType( Serializable ):
    
    def __init__( self, key = None, force_constant = None, phaseShift = None, multiplicity = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        self.force_constant = force_constant

        self.phaseShift = phaseShift

        self.multiplicity = multiplicity


class ImproperType( Serializable ):
    
    def __init__( self, key = None, force_constant = None, angle0 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # key to refer to the type
        self.key = key

        self.force_constant = force_constant

        self.angle0 = angle0


class ForceField( Serializable ):
    
    def __init__( self, key = None, description = None, linkexclusions = None, physicalconstants = None ):
        
        self.key = key
        self.description = description
        self.linkexclusions = linkexclusions
        self.physicalconstants = physicalconstants
        
        self.masstypes     = ContiguousMap()
        self.vdwtypes      = ContiguousMap()
        self.vdwmixed      = ContiguousMap()
        self.special_vdw   = ContiguousMap()
        self.coultypes     = ContiguousMap()
        self.bondtypes     = ContiguousMap()
        self.angletypes    = ContiguousMap()
        self.dihedraltypes = ContiguousMap()
        self.impropertypes = ContiguousMap()