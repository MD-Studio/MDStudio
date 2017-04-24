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

import json

from lie_topology.common.serializable import Serializable
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException

class Atom( Serializable ):
    
    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # Name of the atom
        self.name = None
        
        # Element of the atom
        self.element = None
        
        # Identifier number defined by external sources
        self.identifier = None
        
        # Indicates if this atom is part of the united group
        self.united = None

        # Indicates if this atom is part of an aromatic system
        self.aromatic = None
        
        
class ForceFieldDescription( Serializable ):
    
    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

    	# Mass type, to be combined with a force field input
        self.mass_type = None
        
        # Van der waals type, to be combined with a force field input
        self.vdw_type = None
        
        # Coulombic type, to be combined with a force field input
        self.coulombic_type = None
        
        # Charge group indiciation
        self.charge_group = None
        
        # Exclusion assignment, may include external atoms in chains
        self.exclusions = None
        
        # Virtual site treatment
        self.virtual_site = None
        
        
class ForceFieldAtom( Atom ):
    
    def __init__( self ):
        
        # Call the base classes constructor with the parameters it needs
        Atom.__init__( self, self.__module__, self.__class__.__name__ )
    	Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        # Description for an all atom treatment
        self.all_atom_parameters = None
        
        # Description for an united atom 
        self.united_atom_parameters = None