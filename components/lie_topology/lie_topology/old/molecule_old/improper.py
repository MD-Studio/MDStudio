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

from copy import deepcopy

from lie_topology.common.serializable import Serializable
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.bondedTerm import BondedTerm
from lie_topology.molecule.reference import AtomReference
from lie_topology.forcefield.forcefield import ImproperType
from lie_topology.forcefield.reference import ForceFieldReference

class Improper( BondedTerm ):
    
    def __init__( self, atom_references = None, forcefield_type = None, united = None ):
        
        # Call the base class constructor with the parameters it needs
        BondedTerm.__init__(self, self.__module__, self.__class__.__name__, 4, atom_references, forcefield_type )
    
    def SafeCopy(self, molecule_key=None, group_key=None):

        forcefield_type = deepcopy( self._forcefield_type )

        # if force field object just store the key for now
        if isinstance(forcefield_type,ImproperType):
            forcefield_type = ForceFieldReference( key=forcefield_type.key )

        return Improper( atom_references=self._SafeCopyReferences(molecule_key, group_key), forcefield_type=forcefield_type )

    def Debug(self):

        safe_ref_1 = "?"
        safe_ref_2 = "?"
        safe_ref_3 = "?"
        safe_ref_4 = "?"
        safe_forcefield_type = "?"

        if self._atom_references and len(self._atom_references) == 4:
            safe_ref_1 = self._DebugRef( self._atom_references[0] )
            safe_ref_2 = self._DebugRef( self._atom_references[1] )
            safe_ref_3 = self._DebugRef( self._atom_references[2] )
            safe_ref_4 = self._DebugRef( self._atom_references[3] )

        if self._forcefield_type:
            if isinstance(self._forcefield_type, ImproperType):
                safe_forcefield_type = "%s" % (self._forcefield_type.key)
            else:
                safe_forcefield_type = "%s*" % (self._forcefield_type.key)

        # Indicates the bond order of this bond
        return "impr %-25s %-25s %-25s %-25s %7s\n" % (safe_ref_1, safe_ref_2, safe_ref_3, safe_ref_4, 
                                                       safe_forcefield_type)