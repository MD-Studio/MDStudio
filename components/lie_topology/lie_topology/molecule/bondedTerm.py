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
from lie_topology.common.exception import LieTopologyException

from lie_topology.molecule.atom import Atom

class BondedTerm( Serializable ):
    
    def __init__( self, imodule, iclass, references_size, atom_references, forcefield_type ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, imodule, iclass )

        self._references_size = references_size

        # Indices of the atoms involved in the bond, length should be 2
        self._atom_references = atom_references
    
        # Bond type in the force field
        self._forcefield_type = forcefield_type

    @property
    def forcefield_type(self):

        return self._forcefield_type

    @property
    def atom_references(self):

        return self._atom_references

    @atom_references.setter
    def atom_references(self, value):

        if len(value) != self._references_size:
            raise LieTopologyException( "BondedTerm::atom_references", "Tried to set atom_references with len %i while expected len %i"
                                        % ( len(value), self._references_size ) )

        self._atom_references = value

    @forcefield_type.setter
    def forcefield_type(self, value):

        self._forcefield_type = value

    def IsReferenceResolved(self):

        reponse=True

        for atom_reference in self._atom_references:
            if not isinstance(atom_reference, Atom):
                reponse=False
                break
        
        return reponse

    def ReKeyReferences( self,
                         old_atom_key = None, new_atom_key = None, 
                         old_molecule_key = None, new_molecule_key = None,
                         old_group_key = None, new_group_key = None ):

        for reference in self._atom_references:

            if old_atom_key is not None and new_atom_key is not None:
                if reference.atom_key == old_atom_key:
                    reference.atom_key = new_atom_key

            if old_molecule_key is not None and new_molecule_key is not None:
                if reference.molecule_key == old_molecule_key:
                    reference.molecule_key = new_molecule_key

            if old_group_key is not None and new_group_key is not None:
                if reference.group_key == old_group_key:
                    reference.group_key = new_group_key

    def _SafeCopyReferences(self, molecule_key = None, group_key = None):

        new_references=[]
        for atom_link in self._atom_references:
            new_reference = atom_link.ToReference()

            if molecule_key is not None:
                new_reference.molecule_key = molecule_key
            
            if group_key is not None:
                new_reference.group_key = group_key

            new_references.append( new_reference )
        
        return new_references
    
    def _DebugRef(self, atom_ref):

        response = "?"

        if isinstance(atom_ref, Atom):
            response = atom_ref.ToReference().Debug()
        else:
            # mark as not yet resolved
            response = "%s*" % (  atom_ref. Debug() )
        
        return response
