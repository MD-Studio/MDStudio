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
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException

class AtomReference( Serializable ):
    
    def __init__( self, group_key=None, molecule_key=None, atom_key=None, external_index=None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        self._group_key = group_key

        self._molecule_key = molecule_key

        self._atom_key = atom_key

        # index of the atm
        self._external_index = external_index
    
    @property
    def group_key(self):
        return self._group_key

    @property 
    def molecule_key(self):
        return self._molecule_key

    @property
    def atom_key(self):
        return self._atom_key
    
    @group_key.setter
    def group_key(self,value):
        self._group_key = value

    @molecule_key.setter
    def molecule_key(self,value):
        self._molecule_key = value

    @atom_key.setter
    def atom_key(self,value):
        self._atom_key = value

    def TryLink( self, root, referencing_molecule ):
        
        ## Try to find the linking atom
        ## While the molecule includes this reference
        ## in e.g. a bond, this reference could still point
        ## to a different molecule
        target_molecule = None
        target_group = None

        if self._group_key:
            # if we have a groupname find the root

            if root is None:
                raise LieTopologyException("AtomReference::UpcastFromMolecule", "a valid root object wasnt passed")
                
            target_group = root.groups[self._group_key]

        if self._molecule_key:

            if target_group is None:

                if self._molecule_key == referencing_molecule.key:
                    target_molecule = referencing_molecule

                else:
                    raise LieTopologyException("AtomReference::UpcastFromMolecule", "molecule does not contain a group reference")
            
            else:
                target_molecule = target_group.molecules[self._molecule_key]
        
        if self._atom_key is None or\
           target_molecule is None:
            return self

        return target_molecule.atoms[self._atom_key]
    
    def Debug(self):

        if self._external_index:
            return "(%i)" % (self._external_index)
        
        else:
            safe_atom_key= self._atom_key if self._atom_key is not None else "?"
            safe_group_key = self._group_key if self._group_key is not None else "?" 
            safe_molecule_key = self._molecule_key if self._molecule_key is not None else "?" 

            return "(%s,%s,%s)" % (safe_atom_key,safe_molecule_key,safe_group_key)