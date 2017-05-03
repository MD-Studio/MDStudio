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
    
    def __init__( self, name = None, element = None, identifier = None, aromatic = None,\
                  occupancy = None, bfactor = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # Name of the atom
        self.name = name
        
        # Element of the atom
        self.element = element
        
        # Identifier number defined by external sources
        self.identifier = identifier
        
        # Indicates if this atom is part of an aromatic system
        self.aromatic = aromatic
        
        # If from a crystallographic source store the occupancy
        self.occupancy = occupancy

        # If from a crystallographic source store the bfactor
        self.bfactor = bfactor

        # Mass type, to be combined with a force field input
        self.mass_type = None
        
        # Van der waals type, to be combined with a force field input
        self.vdw_type = None
        
        # Coulombic type, to be combined with a force field input
        # NOTE, cane be either a direct charge OR 
        self.coulombic_type = None
        
        # Polarizability type, to be combined with a force field input
        self.polarizable_type = None

        # Charge group indiciation
        self.charge_group = None
        
        # Virtual site treatment
        self.virtual_site = None

