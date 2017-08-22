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

class Blueprint( Serializable ):

    def __init__(self, title = None, exclusion_distance = None):

        self._title = title

        self._exclusion_distance = exclusion_distance

        # Physical constants
        self._physical_constants = PhysicalConstants()
        
        # Solutes present in the mtb
        self._molecules = ContiguousMap()

        # Blends present in the mtb
        self._variants = ContiguousMap()

        # Blends present in the mtb
        self._variant_templates = ContiguousMap()

        # Solvents present in the mtb
        self._solvents = ContiguousMap()

    @property
    def title(self):

        return self._title

    @property
    def exclusion_distance(self):

        return self._exclusion_distance

    @property
    def physical_constants(self):

        return self._physical_constants

    @property
    def molecules(self):

        return self._molecules

    @property
    def solvents(self):

        return self._solvents

    @title.setter
    def title(self, value):

        self._title = value

    @exclusion_distance.setter
    def exclusion_distance(self, value):

        self._exclusion_distance = value

    def AddMolecule( self, **kwargs ):
  
        if  "molecule" in kwargs:
            molecule = kwargs["molecule"]
            if not molecule.key:
                raise LieTopologyException("Blueprint::AddMolecule", "key is a required argument" )

            self._molecules.insert( molecule.key, molecule )

        else:
            kwargs["parent"] = self
            self._molecules.insert( kwargs["key"], Molecule(**kwargs) )
    
    def UpdateVariantList( self, molecule_key, variant_list ):

        if  molecule_key in self._variants:
            self._variants[molecule_key].update( variant_list )

        else: 
            self._variants.insert( molecule_key, variant_list )

    def AddVariantTemplate( self, **kwargs ):
  
        if  "molecule" in kwargs:
            molecule = kwargs["molecule"]
            if not molecule.key:
                raise LieTopologyException("Blueprint::AddBlend", "key is a required argument" )

            self._variant_templates.insert( molecule.key, molecule )

        else:
            kwargs["parent"] = self
            self._variant_templates.insert( kwargs["key"], Molecule(**kwargs) )

    def AddSolvent( self, **kwargs ):

        if "molecule" in kwargs:

            molecule = kwargs["molecule"]
            if not molecule.key:
                raise LieTopologyException("Blueprint::AddSolvent", "key is a required argument" )

            self._solvents.insert( molecule.key, kwargs["molecule"] )

        else:
            if not "key" in kwargs:
                raise LieTopologyException("Blueprint::AddSolvent", "key is a required argument" )
            
            self._solvents.insert( kwargs["key"], Molecule( **kwargs ) )


    def MoleculeVariants( self, molecule_key ):
    
        output_list={}
    
        if molecule_key in self._variants:
            output_list = self._variants[molecule_key]

        return output_list

    def FindMolecule( self, molecule_key ):

        return self._molecules.find( molecule_key )

    def FindVariant( self, blend_name ):

        return self._variant_templates.find( blend_name )

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
        
        # patch bonded references
        for group in self._groups.values():
            for molecule in group.molecules.values():
                molecule.ResolveReferences( self )
        
        for solvent in self._solvents.values():
            solvent.ResolveReferences( None )