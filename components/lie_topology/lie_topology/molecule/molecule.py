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

from copy import deepcopy

from lie_topology.common.serializable  import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception     import LieTopologyException
from lie_topology.molecule.atom        import Atom
from lie_topology.molecule.bond        import Bond
from lie_topology.molecule.angle       import Angle
from lie_topology.molecule.dihedral    import Dihedral
from lie_topology.molecule.reference   import AtomReference

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
        self._bonds = bonds if bonds is not None else []
        
        # Angles of this solute
        self._angles = angles if angles is not None else []
        
        # Dihedrals of this solute
        self._dihedrals = dihedrals if dihedrals is not None else []
        
        # Impropers of this solute
        self._impropers = impropers if impropers is not None else []

    def AddAtom(self, prepend=False, **kwargs  ):
        
        key = None
        atom = None

        if "atom" in kwargs:
            atom = kwargs["atom"]
            atom.molecule = self
            key = atom.key

        else:  
            if not "key" in kwargs:
                raise LieTopologyException("Molecule::AddAtom", "Key is a required argument" )

            kwargs["parent"] = self
            key  = kwargs["key"]
            atom = Atom(**kwargs)

        index = 0 if prepend is True else self.atoms.size()   
        self.atoms.insert(key, atom, index=index )

    def _IndexOfBonded( self, test_list, bonded):

        reponse=-1

        # atom references could be both Atoms and AtomReferences
        # thats why we make an additional list
        bonded_ref = []
        
        for atom_ref in bonded.atom_references:
            bonded_ref.append(atom_ref.ToReference().hash)
        
        index=0
        for test_item in test_list:
            test_ref = []

            for atom_ref in test_item.atom_references:
                test_ref.append(atom_ref.ToReference().hash)
        
            # found a collition
            if len( set(bonded_ref) & set(test_ref) ) == len( test_item.atom_references ):
                reponse=index
                break
            
            index+=1

        return reponse

    def IndexOfBond(self, bond ):

        return self._IndexOfBonded( self.bonds, bond )
    
    def IndexOfAngle(self, angle ):

        return self._IndexOfBonded( self.angles, angle )

    def IndexOfDihedral(self, dihedral ):

        return self._IndexOfBonded( self.dihedrals, dihedral )

    def IndexOfImproper(self, improper ):

        return self._IndexOfBonded( self.impropers, improper )

    def AddBond( self, bond ):

        #perform a sanity check if this bond is not already processed
        if len(bond.atom_references) != 2:
            raise LieTopologyException("Molecule::AddBond", "Can only add bonds that have 2 atom references" )
        
        # if not present yet
        if self.IndexOfBond(bond) < 0:
            self._bonds.append( bond )

    def AddAngle( self, angle ):

        #perform a sanity check if this bond is not already processed
        if len(angle.atom_references) != 3:
            raise LieTopologyException("Molecule::AddAngle", "Can only add angles that have 3 atom references" )

        self._angles.append( angle )

    def AddImproper( self, improper ):

        #perform a sanity check if this bond is not already processed
        if len(improper.atom_references) != 4:
            raise LieTopologyException("Molecule::AddImproper", "Can only add impropers that have 4 atom references" )

        self._impropers.append( improper )
    
    def AddDihedral( self, dihedral ):

        #perform a sanity check if this bond is not already processed
        if len(dihedral.atom_references) != 4:
            raise LieTopologyException("Molecule::AddDihedral", "Can only add dihedrals that have 4 atom references" )

        self._dihedrals.append( dihedral )

    def IndexOfAtom( self, atom_key ):

        if not atom_key in self._atoms:
            raise LieTopologyException("Molecule::AddAtom", "A linked molecule does not contain the parent atom" )

        index = self._atoms.indexOf(atom_key)

        if self._group and index >= 0:
            index += self._group.AtomIndexStartOfMolecule(self._key)

        return index
    
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

    

    # these are standard named reference that result from
    # a serialization
    def ResolveReferences( self, root_obj ):

        # next thing we want to do is attach bonded connections
        for cat in["_bonds", "_angles", "_impropers", "_dihedrals"]:
            category = self.__dict__[cat]

            if not category is None:
                for item in category:

                    new_references = []
                    for reference in item.atom_references:
                        
                        # in this step we resolve the named reference objects to
                        # actual atom objects
                        if isinstance(reference, AtomReference):   
                            new_reference = reference.TryLink(root_obj, self)
                            new_references.append( new_reference )

                        else:
                            new_references.append( reference, new_reference.Debug() )
                    
                    item.atom_references = new_references

    def _SafeCopyAtoms(self, dest_molecule):
        # add atoms
        #for key, atom in src_molecule.atoms.items():
        for key, atom in self._atoms.items():

            dest_molecule.AddAtom( atom=atom.SafeCopy() )
                                   
    def _SafeCopyBonded(self, dest_molecule, molecule_key):

        for bond in self._bonds:
            dest_molecule.AddBond( bond.SafeCopy(molecule_key) )
        
        for angle in self._angles:
            dest_molecule.AddAngle( angle.SafeCopy(molecule_key) )
        
        for dihedral in self._dihedrals:
            dest_molecule.AddDihedral( dihedral.SafeCopy(molecule_key) )
        
        for improper in self._impropers:
            dest_molecule.AddImproper( improper.SafeCopy(molecule_key) )

    def SafeCopy(self, molecule_key=None):

        if molecule_key is None:
            molecule_key = self._key

        # start by making a new molecule
        molecule_cpy = Molecule( key=molecule_key, type_name=self._type_name, identifier=self._identifier )

        # next replace all direct obj references with indirect ones
        self._SafeCopyAtoms(molecule_cpy)
        self._SafeCopyBonded(molecule_cpy, molecule_key)

        return molecule_cpy

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
    

    def Debug(self):

        key = str(self._key) if self._key is not None else "?"
        type_name = str(self._type_name) if self._type_name is not None else "?"
        identifier = str(self._identifier) if self._identifier is not None else "?"

        aggregate = "%7s %7s %7s\n" % (key, type_name, identifier)
        index=1
        for atom in self._atoms.values():
            aggregate+="\t%7i %s" % ( index, atom.Debug() )
            index+=1

        index=1
        for bond in self._bonds:
            aggregate+="\t%7i %s" % ( index, bond.Debug() )
            index+=1

        index=1
        for angle in self._angles:
            aggregate+="\t%7i %s" % ( index, angle.Debug() )
            index+=1

        index=1
        for improper in self._impropers:
            aggregate+="\t%7i %s" % ( index, improper.Debug() )
            index+=1
        
        index=1
        for dihedral in self._dihedrals:
            aggregate+="\t%7i %s" % ( index, dihedral.Debug() )
            index+=1

        return aggregate