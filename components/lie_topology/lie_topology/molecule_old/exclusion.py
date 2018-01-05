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

from lie_topology.common.serializable import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.bondedTerm import BondedTerm

class Exclusion( BondedTerm ):
    
    def __init__( self, atom_references=None ):
        
        # Call the base class constructor with the parameters it needs
        BondedTerm.__init__(self, self.__module__, self.__class__.__name__, 2,  atom_references, None )

    def SafeCopy(self, molecule_key=None, group_key=None):

        forcefield_type = deepcopy( self._forcefield_type )

        return Exclusion( atom_references=self._SafeCopyReferences(molecule_key,group_key) )