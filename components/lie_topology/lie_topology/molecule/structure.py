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

from lie_topology.common.serializable import Serializable, IsBasicMap, IsNumpyType
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.topology import Topology
from lie_topology.molecule.crystal import Lattice

class Time( Serializable ):
    
    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # indentifier of the model
        self.model_number = None
        
        # recording time
        self.time = None

class Structure( Serializable ):
    
    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )

        # Name of the structure
        self.name = None

        # Name of the 
        self.description = None

        # Time of recording
        self.step = None

        # numpy array with xyz coordinates
        self.coordinates = None
        
        # numpy array with xyz velocities
        self.velocities = None
        
        # numpy array with xyz cos-positions
        self.cos_offsets = None
        
        # numpy array with lattice shifts
        self.lattice_shifs = None

        # numpy array with xyz forces
        self.forces = None
        
        # topology
        self.topology = None

        # lattice information
        self.lattice = None

    def OnSerialize( self, logger = None ):   

        result = {}
        
        for itemName in ("name", "description" ):
            item = self.__dict__[itemName]
            if item:
                result[itemName] = item

        for itemName in ("step", "topology", "lattice" ):
            item = self.__dict__[itemName]
            if item:
                result[itemName] = item.OnSerialize(logger)

        for itemName in ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ):
            item = self.__dict__[itemName]
            if IsNumpyType(item):
                result[itemName] = item.tolist()

        return result
    
    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Structure::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Structure::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        for itemName in ("name", "description" ):
            
            if itemName in data:
                item = data[itemName]
                self.__dict__[itemName] = item

        if "step" in data:
            self.step = Time()
            self.step.OnDeserialize(data["step"], logger)

        if "topology" in data:
            self.topology = Topology()
            self.topology.OnDeserialize(data["topology"], logger)
        
        if "lattice" in data:
            self.lattice = Lattice()
            self.lattice.OnDeserialize(data["lattice"], logger)

        for itemName in ("coordinates", "velocities", "cos_offsets", "lattice_shifs", "forces" ):

            if itemName in data:
                item = data[itemName]
                self.__dict__[itemName] = np.array( item )