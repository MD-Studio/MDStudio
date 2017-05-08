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

class CoulombicType( Serializable ):
    
    def __init__( self, name = None, charge = None, polarizability = None, cos_charge = None,\
                  damping_level = None, damping_power = None  ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the charge type
        self.name = name

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
    
    def __init__( self, c6 = None, c6_14 = None, c12 = None, c12_14 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.c6     = c6
        self.c6_14  = c6_14
        self.c12    = c12
        self.c12_14 = c12_14
        self.matrix = dict()
        

class VdwMixed( Serializable ):
    
    def __init__( self, c6 = None, c6_14 = None, c12 = None, c12_14 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        self.types = []
        self.c6     = c6
        self.c6_14  = c6_14
        self.c12    = c12
        self.c12_14 = c12_14
        
class MassType( Serializable ):
    
    def __init__( self, name = None, identifier = None, mass = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.identifier = identifier
        self.mass       = mass
      
class BondType( Serializable ):
    
    def __init__( self, name = None, fc_quartic = None, fc_harmonic = None, b0 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.fc_quartic = fc_quartic
        self.fc_harmonic = fc_harmonic
        self.b0 = b0
    
        
class AngleType( Serializable ):
    
    def __init__( self, name = None, fc_non_harmonic = None, fc_harmonic = None, angle0 = None  ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.fc_non_harmonic = fc_non_harmonic
        self.fc_harmonic = fc_harmonic
        self.angle0 = angle0
    

class DihedralType( Serializable ):
    
    def __init__( self, name = None, fc = None, phaseShift = None, multiplicity = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.fc = fc
        self.phaseShift = phaseShift
        self.multiplicity = multiplicity


class ImproperType( Serializable ):
    
    def __init__( self, name = None, fc = None, angle0 = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # name to refer to the type
        self.name = name

        self.fc = fc
        self.angle0 = angle0