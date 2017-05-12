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
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.reference import AtomReference
from lie_topology.forcefield.forcefield import DihedralType,ImproperType
from lie_topology.forcefield.reference import ForceFieldReference

class Dihedral( Serializable ):
    
    def __init__( self, atom_references = [], dihedral_type = None, united = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Indices of the atoms involved in the dihedral, length should be 4
        self._atom_references = atom_references
        
        # Dihedral type in the force field
        self._dihedral_type = dihedral_type
    
    @property
    def atom_references(self):

        return self._atom_references

    @property
    def dihedral_type(self):

        return self._dihedral_type

    @atom_references.setter
    def atom_references(self, value):

        self._atom_references = value

    def OnSerialize( self, logger = None ):   

        result = {}
        
        if not (self._atom_references is None):

            ser_values = []
            for item in self._atom_references:

                if isinstance(item, Atom):
                    item = item.ToReference()

                ser_values.append( item.OnSerialize(logger) )

            result["atom_references"] = ser_values
        
        if self._dihedral_type:

            type_str = None
            if isinstance(self._dihedral_type, ForceFieldReference):
                type_str = self._dihedral_type.name

            elif isinstance(self._dihedral_type, (DihedralType, ImproperType)):
                type_str = self._dihedral_type.OnSerialize(logger)
                
            else:
                print(self._dihedral_type)
                raise LieTopologyException("Dihedral::OnSerialize","Unknown dihedral type") 
        
            result["dihedral_type"] = type_str    

        return result

    def OnDeserialize( self, data, logger = None ):

        if "atom_references" in data:
            self._atom_references = []

            for reference in data["atom_references"]:

                if not isinstance(reference, dict):
                    raise LieTopologyException("Dihedral::OnDeserialize","Unknown dihedral reference") 
                    
                ref_obj = AtomReference()
                ref_obj.OnDeserialize(reference, logger)
                
                self._atom_references.append(ref_obj)
                
        if "dihedral_type" in data:
            localData = data["dihedral_type"]

            if isinstance(localData, str):
                self._dihedral_type = ForceFieldReference( name=localData )

            elif isinstance(localData, dict):
                self._dihedral_type = DihedralType()
                self._dihedral_type.OnDeserialize(localData, logger)
                
            else:
                 raise LieTopologyException("Dihedral::OnSerialize","Unknown dihedral type") 