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

from lie_topology.common.serializable import Serializable, IsBasicMap
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.group import Group 
from lie_topology.molecule.molecule import Molecule

class Topology( Serializable ):
    
    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        # Solutes present in this topology
        self.groups = ContiguousMap()

        # Solvent present in this topology
        self.solvent = None

    def AddGroup( self, **kwargs ):

        if not "name" in kwargs:

            raise LieTopologyException("Topology::AddGroup", "Name is a required argument" )

        self.groups.insert( kwargs["name"], Group( **kwargs ) )

    def GetGroup( self, name ):

        return self.groups[name]
    
    def OnSerialize( self, logger = None ):   

        result = {}
        
        if self.groups:
            ser_keys = []
            ser_groups = []
            
            for ikey, igroup in self.groups.items():
                ser_keys.append( ikey )
                ser_groups.append( igroup.OnSerialize(logger) )
                
            result["groups"] = { "keys" : ser_keys, "values" : ser_groups }

        if self.solvent:

            ser_solvent = self.solvent.OnSerialize(logger)
            result["solvent"] = ser_solvent
        
        return result
    
    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Topology::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Serializable::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        if "groups" in data:
            
            groupData = data["groups"]
            groupData_keys = groupData["keys"]
            groupData_values = groupData["values"]
            
            if len(groupData_keys) != len(groupData_values):
                raise LieTopologyException( "Topology::OnDeserialize", "For group data, number of keys did not match number of items" )

            for i in range(0,len(groupData_keys) ):

                key = groupData_keys[i]
                item = groupData_values[i]

                group = Group()
                group.OnDeserialize(item, logger)

                self.groups.insert( key, group )
            
        if "solvent" in data:
            
            self.solvent = Molecule()
            self.solvent.OnDeserialize(data["solvent"], logger)


                    