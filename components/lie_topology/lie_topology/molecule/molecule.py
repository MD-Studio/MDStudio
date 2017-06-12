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
    
    def __init__( self, parent = None, key = None, type_name = None, identifier = None, \
                  bonds = None, angles = None, dihedrals = None, impropers = None, replacing = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Parent group of this molecule
        self._group = parent

        # key of the solutes, must be unique
        self._key = key
        
        # Type name of the molecule (e.g. for residues GLY,GLU etc.)
        self._type_name = type_name

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

        if not "key" in kwargs:

            raise LieTopologyException("Molecule::AddAtom", "Key is a required argument" )
        
        kwargs["parent"] = self
        self.atoms.insert(kwargs["key"], Atom(**kwargs) )
    
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
    def atom_count(self):
        return self._atoms.size()

    @property
    def preceding_count(self):
        num=0
        for atom in self._atoms.values():
            if atom.preceding is True:
                num+=1
        return num

    @property
    def trailing_count(self):
        num=0
        for atom in self._atoms.values():
            if atom.trailing is True:
                num+=1
        return num

    @property
    def group(self):

        return self._group

    @property
    def key(self):

        return self._key
    
    @property
    def type_name(self):

        return self._type_name
        
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
        
        SerializeFlatTypes( ["key", "identifier"], self.__dict__, result, '_' )
        SerializeContiguousMaps( ["atoms"], self.__dict__, result, logger, '_' )
        SerializeObjArrays( ["bonds", "angles", "impropers", "dihedrals"],  self.__dict__, result, logger, '_' )

        return result

    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Molecule::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Molecule::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeFlatTypes( ["key", "identifier"], data, self.__dict__, '_' )
        DeserializeContiguousMapsTypes( ["atoms"], [Atom], data, self.__dict__, logger, '_', self  )
        DeserializeObjArrays( ["bonds", "angles", "impropers", "dihedrals"],\
                              [ Bond, Angle, Dihedral, Dihedral ],\
                              data, self.__dict__, logger, '_')
    
    # these are standard named reference that result from
    # a serialization
    def ResolveNamedReferences( self, root_obj ):

        # next thing we want to do is attach bonded connections
        for cat in["_bonds", "_angles", "_impropers", "_dihedrals"]:
            category = self.__dict__[cat]

            if not category is None:
                for item in category:

                    new_references = []
                    for ref in item.atom_references:

                        # in this step we resolve the named reference objects to
                        # actual atom objects
                        new_references.append( ref.TryLink(root_obj, self) )
                    
                    item.atom_references = new_references

    
    def Debug(self):

        key = str(self._key) if self._key is not None else "?"
        type_name = str(self._type_name) if self._type_name is not None else "?"
        identifier = str(self._identifier) if self._identifier is not None else "?"

        aggregate = "%7s %7s %7s\n" % (key, type_name, identifier)
        for atom in self._atoms.values():

            aggregate+="\t"+atom.Debug()
        
        for bond in self._bonds:
            aggregate+="\t"+bond.Debug()

        for angle in self._angles:
            aggregate+="\t"+angle.Debug()

        return aggregate