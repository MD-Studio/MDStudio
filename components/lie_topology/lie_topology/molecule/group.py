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
from lie_topology.molecule.molecule import Molecule 

class Group( Serializable ):
    
    def __init__( self, parent = None, name = None, chain_id  = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        self._parent = parent

        # full name of the group
        self._name = name

        # chainid like in pdb
        self._chain_id = chain_id 

        # Solutes present in this topology
        self._molecules = list()


    @property
    def name(self):

        return self._name

    @property
    def chain_id(self):

        return self._chain_id

    @property
    def molecules(self):

        return self._molecules

    def AddMolecule( self, **kwargs ):
        
        kwargs["parent"] = self
        if  "molecule" in kwargs:
            self._molecules.append(kwargs["molecule"])

        else:
            self._molecules.append( Molecule(**kwargs) )

    def GetSolutesByName( self, name ):

        olist = []

        for solute in self._molecules:

            if solute.name == name:

                olist.append(solute)

        return olist
    
    def GetSoluteByIndex( self, index ):
    
        return self._molecules[index]