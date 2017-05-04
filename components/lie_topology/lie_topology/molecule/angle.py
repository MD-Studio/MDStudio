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

class Angle( Serializable ):
    
    def __init__( self, atom_names = None, angle_type = None, united = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Indices of the atoms involved in the angle, length should be 3
        self.atom_names = atom_names
        
        # Angle type in the force field
        self.angle_type = angle_type
        
        # Indicates if this angle is part of the united atom system
        self.united = united
        
    
    