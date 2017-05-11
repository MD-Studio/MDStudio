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
from lie_topology.forcefield.forcefield import BondType

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

            ser_keys = []
            
            for item in self._atom_references:

                if isinstance(item, str):
                    ser_keys.append( item )

                elif isinstance(item, Atom):
                    ser_keys.append( item.name )
                
                else:
                    ser_keys.append( item.OnSerialize(logger) )

            result["atom_references"] = ser_keys
        
        if self._bond_type:

            type_str = None
            if isinstance(self._bond_type, str):
                type_str = self._bond_type

            elif isinstance(self._bond_type, BondType):
                type_str = self._bond_type.name
                
            else:
                 type_str = self._bond_type.OnSerialize(logger)
        
            result["bond_type"] = type_str    

        for itemName in ("aromatic", "bond_order"):
            item = self.__dict__["_%s" % ( itemName )]
            if item:
                result[itemName] = item

        return result
    
    