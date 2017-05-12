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
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.reference import AtomReference
from lie_topology.forcefield.forcefield import BondType
from lie_topology.forcefield.reference import ForceFieldReference

class Bond( Serializable ):
    
    def __init__( self, atom_references=None, bond_type=None, aromatic=None, bond_order=None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Indices of the atoms involved in the bond, length should be 2
        self._atom_references = atom_references
        
        # Bond type in the force field
        self._bond_type = bond_type
        
        # Indicates if this bond is part of an aromatic system
        self._aromatic = aromatic
        
        # Indicates the bond order of this bond
        self._bond_order = bond_order
        
    def OnSerialize( self, logger = None ):   

        result = {}
        
        if not (self._atom_references is None):

            ser_values = []
            for item in self._atom_references:

                if isinstance(item, Atom):
                    item = item.ToReference()

                ser_values.append( item.OnSerialize(logger) )

            result["atom_references"] = ser_values
        
        if self._bond_type:

            type_str = None
            if isinstance(self._bond_type, ForceFieldReference):
                type_str = self._bond_type.name

            elif isinstance(self._bond_type, BondType):
                type_str = self._bond_type.OnSerialize(logger)
                
            else:
                print(self._bond_type)
                raise LieTopologyException("Bond::OnSerialize","Unknown bond type") 
        
            result["bond_type"] = type_str    

        
        SerializeFlatTypes( ["aromatic", "bond_order"], self.__dict__, result, '_' )

        return result

    def OnDeserialize( self, data, logger = None ):

        if "atom_references" in data:
            self._atom_references = []

            for reference in data["atom_references"]:

                if not isinstance(reference, dict):
                    raise LieTopologyException("Bond::OnDeserialize","Unknown bond reference") 
                    
                ref_obj = AtomReference()
                ref_obj.OnDeserialize(reference, logger)
                
                self._atom_references.append(ref_obj)

        if "bond_type" in data:
            localData = data["bond_type"]

            if isinstance(localData, str):
                self._bond_type = ForceFieldReference( name=localData )

            elif isinstance(localData, dict):
                self._bond_type = BondType()
                self._bond_type.OnDeserialize(localData, logger)
                
            else:
                 raise LieTopologyException("Bond::OnSerialize","Unknown bond type") 


        DeserializeFlatTypes( ["aromatic", "bond_order"], data, self.__dict__, '_' )
    
    