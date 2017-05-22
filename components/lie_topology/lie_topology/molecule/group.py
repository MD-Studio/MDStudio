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

from lie_topology.common.serializable import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.molecule import Molecule 

class Group( Serializable ):
    
    def __init__( self, parent = None, key = None, chain_id  = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        # parent topology
        self._parent = parent

        # full key of the group
        self._key = key

        # chainid like in pdb
        self._chain_id = chain_id 

        # Solutes present in this topology
        self._molecules = ContiguousMap()

    @property
    def atom_count(self):
        count = 0
        
        for molecule in self._molecules.values():
            count += molecule.atom_count
        
        return count

    @property
    def parent(self):

        return self._parent

    @property
    def key(self):

        return self._key

    @property
    def chain_id(self):

        return self._chain_id

    @property
    def molecules(self):

        return self._molecules

    @parent.setter
    def parent(self, value):

        self._parent = value


    def AddMolecule( self, **kwargs ):
  
        if  "molecule" in kwargs:
            molecule = kwargs["molecule"]
            molecule.group = self
            self._molecules.insert( molecule.key, molecule )

        else:
            kwargs["parent"] = self
            self._molecules.insert( kwargs["key"], Molecule(**kwargs) )

    def GetSoluteByKey( self,  ):

        result = None

        if key in self._molecules:

            result = solute

        return result
    
    def GetSoluteByIndex( self, index ):
    
        return self._molecules.at(index)
    
    def OnSerialize( self, logger = None ):   

        result = {}
        
        SerializeFlatTypes( ["key", "chain_id"], self.__dict__, result, '_' )
        SerializeContiguousMaps( ["molecules"], self.__dict__, result, logger, '_' )

        return result

    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Group::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Group::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeFlatTypes( ["key", "chain_id"], data, self.__dict__, '_' )
        DeserializeContiguousMapsTypes( ["molecules"], [Molecule], data, self.__dict__, logger, '_', self )

