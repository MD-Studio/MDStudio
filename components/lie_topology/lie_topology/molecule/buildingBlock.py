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

import sys
import os
import numpy as np

from lie_topology.common.serializable  import *
from lie_topology.common.exception     import LieTopologyException
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.forcefield.physconst import PhysicalConstants
from lie_topology.molecule.group       import Group 
from lie_topology.molecule.molecule    import Molecule

class BuildingBlock( Serializable ):

    def __init__(self, title = None, exclusion_distance = None):

        self._title = title

        self._exclusion_distance = exclusion_distance

        # Physical constants
        self._physical_constants = PhysicalConstants()
        
        # Solutes present in the mtb
        self._groups = ContiguousMap()

        # Solvents present in the mtb
        self._solvents = ContiguousMap()

    def AddGroup( self, **kwargs ):

        if not "name" in kwargs:

            raise LieTopologyException("BuildingBlock::AddGroup", "Name is a required argument" )
        
        kwargs["parent"] = self
        self._groups.insert( kwargs["name"], Group( **kwargs ) )
    
    def AddSolvent( self, **kwargs ):

        if "molecule" in kwargs:

            molecule = kwargs["molecule"]
            if not molecule.name:
                raise LieTopologyException("BuildingBlock::AddSolvent", "Name is a required argument" )

            self._solvents.insert( molecule.name, kwargs["molecule"] )

        else:
            if not "name" in kwargs:
                raise LieTopologyException("BuildingBlock::AddSolvent", "Name is a required argument" )
            
            self._solvents.insert( kwargs["name"], Molecule( **kwargs ) )

    def GroupByName( self, name ):

        return self._groups[name]
    
    def OnSerialize( self, logger = None ):   

        result = {}
        
        SerializeFlatTypes(["title", "exclusion_distance"], self.__dict__, result, '_' )
        SerializeObjTypes( ["physical_constants"], self.__dict__, result, logger, '_' )
        SerializeContiguousMaps( ["groups"], self.__dict__, result, logger, '_' )
        SerializeContiguousMaps( ["solvents"], self.__dict__, result, logger, '_' )

        return result
    
    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Topology::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Serializable::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeFlatTypes( ["title", "exclusion_distance"], data, self.__dict__, '_' )
        DeserializeObjTypes( ["physical_constants"], [PhysicalConstants], data, self.__dict__, logger, '_')
        DeserializeContiguousMapsTypes( ["groups", "solvents"], [Group, Molecule], data, self.__dict__, logger, '_' )
        