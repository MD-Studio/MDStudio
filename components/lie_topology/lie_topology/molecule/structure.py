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

import numpy as np

from lie_topology.common.serializable import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.topology import Topology
from lie_topology.molecule.crystal import Lattice

class Time( Serializable ):
    
    def __init__( self, model_number = None, time = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # indentifier of the model
        self._model_number = model_number
        
        # recording time
        self._time = time

    @property
    def model_number(self):

        return self._model_number

    @property
    def time(self):

        return self._time

class Structure( Serializable ):
    
    def __init__( self, name = None, description = None, step = None, coordinates = None, velocities = None,\
                  cos_offsets = None, lattice_shifs = None, forces = None, topology = None, lattice = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # Name of the structure
        self._name = name

        # Name of the 
        self._description = description

        # Time of recording
        self._step = step

        # numpy array with xyz coordinates
        self._coordinates = coordinates
        
        # numpy array with xyz velocities
        self._velocities = velocities
        
        # numpy array with xyz cos-positions
        self._cos_offsets = cos_offsets
        
        # numpy array with lattice shifts
        self._lattice_shifs = lattice_shifs

        # numpy array with xyz forces
        self._forces = forces
        
        # topology
        self._topology = topology

        # lattice information
        self._lattice = lattice

    @property
    def name(self):

        return self._name

    @property
    def description(self):

        return self._description

    @property
    def step(self):

        return self._step

    @property
    def coordinates(self):

        return self._coordinates

    @property
    def velocities(self):

        return self._velocities

    @property
    def cos_offsets(self):

        return self._cos_offsets

    @property
    def lattice_shifs(self):

        return self._lattice_shifs
    
    @property
    def forces(self):

        return self._forces
    
    @property
    def topology(self):

        return self._topology
    
    @property
    def lattice(self):

        return self._lattice

    #####
    @name.setter
    def name(self, value):

        self._name = value

    @description.setter
    def description(self, value):

        self._description = value

    @step.setter
    def step(self, value):

        self._step = value

    @coordinates.setter
    def coordinates(self, value):

        self._coordinates = value

    @velocities.setter
    def velocities(self, value):

        self._velocities = value

    @cos_offsets.setter
    def cos_offsets(self, value):

        self._cos_offsets = value

    @lattice_shifs.setter
    def lattice_shifs(self, value):

        self._lattice_shifs = value
    
    @forces.setter
    def forces(self, value):

        self._forces = value
    
    @topology.setter
    def topology(self, value):

        self._topology = value

    @topology.setter
    def topology(self, value):

        self._topology = value

    @lattice.setter
    def topology(self, value):

        self._lattice = value

    def OnSerialize( self, logger = None ):   

        result = {}
        
        SerializeFlatTypes( ("name", "description"), self.__dict__, result, '_' )
        SerializeObjTypes( ("step", "topology", "lattice" ), self.__dict__, result, logger, '_' )
        SerializeNumpyTypes( ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ), self.__dict__, result, '_' )
        
        # for itemName in ("name", "description" ):
        #     item = self.__dict__["_%s" % ( itemName )]
        #     if item:
        #         result[itemName] = item

        # for itemName in ("step", "topology", "lattice" ):
        #     item = self.__dict__["_%s" % ( itemName )]
        #     if item:
        #         result[itemName] = item.OnSerialize(logger)

        # for itemName in ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ):
        #     item = self.__dict__["_%s" % ( itemName )]
        #     if IsNumpyType(item):
        #         result[itemName] = item.tolist()

        return result
    
    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Structure::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Structure::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeFlatTypes( ("name", "description" ), data, self.__dict__, '_' )
        DeserializeObjTypes( ("step", "topology", "lattice"), [Time, Topology,Lattice ],\
                             data, self.__dict__, logger, '_')
        DeserializeNumpyTypes( ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ),\
                               data, self.__dict__, '_' )

                        

        # if "step" in data:
        #     self.step = Time()
        #     self.step.OnDeserialize(data["step"], logger)

        # if "topology" in data:
        #     self.topology = Topology()
        #     self.topology.OnDeserialize(data["topology"], logger)
        
        # if "lattice" in data:
        #     self.lattice = Lattice()
        #     self.lattice.OnDeserialize(data["lattice"], logger)

        # for itemName in ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ):

        #     if itemName in data:
        #         item = data[itemName]
        #         self.__dict__["_%s" % ( itemName )] = np.array( item )