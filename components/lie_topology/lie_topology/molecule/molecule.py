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

from lie_topology.common.serializable  import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception     import LieTopologyException
from lie_topology.molecule.atom        import Atom
from lie_topology.molecule.bond        import Bond
from lie_topology.molecule.angle       import Angle
from lie_topology.molecule.dihedral    import Dihedral

class Molecule( Serializable ):
    
    def __init__( self, parent = None, name = None, identifier = None, \
                  bonds = None, angles = None, dihedrals = None, impropers = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Parent group of this molecule
        self._group = parent

        # Name of the solutes
        self._name = name
    
        # Identifier number defined by external sources
        self._identifier = identifier

        # Atoms of this solute
        self._atoms = ContiguousMap()
        
        # Bonds of this solute
        self._bonds = bonds
        
        # Angles of this solute
        self._angles = angles
        
        # Dihedrals of this solute
        self._dihedrals = dihedrals
        
        # Impropers of this solute
        self._impropers = impropers

    def AddAtom(self, **kwargs ):

        if not "name" in kwargs:

            raise LieTopologyException("Molecule::AddAtom", "Name is a required argument" )
        
        kwargs["parent"] = self
        self.atoms.insert(kwargs["name"], Atom(**kwargs) )
    
    def AddBond( self, bond ):

        if not isinstance(self._bonds, list):
            self._bonds = []

        self._bonds.append( bond )

    def AddAngle( self, angle ):

        if not isinstance(self._angles, list):
            self._angles = []

        self._angles.append( angle )

    def AddImproper( self, improper ):

        if not isinstance(self._impropers, list):
            self._impropers = []

        self._impropers.append( improper )
    
    def AddDihedral( self, dihedral ):

        if not isinstance(self._dihedrals, list):
            self._dihedrals = []

        self._dihedrals.append( dihedral )

    @property
    def group(self):

        return self._group

    @property
    def name(self):

        return self._name

    @property
    def identifier(self):

        return self._identifier

    @property
    def atoms(self):

        return self._atoms

    @property
    def bonds(self):

        return self._bonds
    
    @property
    def angles(self):

        return self._angles

    @property
    def dihedrals(self):

        return self._dihedrals

    @property
    def impropers(self):

        return self._impropers

    @group.setter
    def group(self, value):

        self._group = value

    @bonds.setter
    def bonds(self, value):

        self._bonds = value
    
    @angles.setter
    def angles(self, value):

        self._angles = value

    @dihedrals.setter
    def dihedrals(self, value):

        self._dihedrals = value

    @impropers.setter
    def impropers(self, value):

        self._impropers = value

    def OnSerialize( self, logger = None ):   

        result = {}
        
        SerializeFlatTypes( ["name", "identifier"], self.__dict__, result, '_' )
        SerializeContiguousMaps( ["atoms"], self.__dict__, result, logger, '_' )
        SerializeObjArrays( ["bonds", "angles", "impropers", "dihedrals"],  self.__dict__, result, logger, '_' )

        return result

    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Molecule::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Molecule::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeFlatTypes( ["name", "identifier"], data, self.__dict__, '_' )
        DeserializeContiguousMapsTypes( ["atoms"], [Atom], data, self.__dict__, logger, '_', self  )
        DeserializeObjArrays( ["bonds", "angles", "impropers", "dihedrals"],\
                              [ Bond, Angle, Dihedral, Dihedral ],\
                              data, self.__dict__, logger, '_')
