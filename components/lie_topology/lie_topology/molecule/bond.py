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

import json

from enum import Enum

from lie_topology.common.serializable import *
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.reference import AtomReference
from lie_topology.forcefield.forcefield import BondType
from lie_topology.forcefield.reference import ForceFieldReference

class SybelBond(Enum):
    single = 1
    double = 2
    triple = 3 
    aromatic = 4
    amide = 5

    def FromString( istr ):

        rvalue = None

        if istr == "1" or istr == "2" or istr == "3":
            rvalue = int(istr)

        elif istr == "ar":
            rvalue = SybelBond.aromatic

        elif istr == "am":
            rvalue = SybelBond.amide

        else:   
            raise LieTopologyException("SybelBond::FromString", "Unknown type %s" %(istr))
    
        return rvalue

    def ToString( ienum ):

        rvalue = None

        if istr >= SybelBond.single and\
           istr <= SybelBond.triple:
            rvalue = str(ienum)

        elif istr == SybelBond.aromatic:
            rvalue = "ar"

        elif istr == SybelBond.amide:
            rvalue = "am"

        else:   
            raise LieTopologyException("SybelBond::ToString", "Unknown type %i" %(ienum))

        return rvalue

class Bond( Serializable ):
    
    def __init__( self, atom_references=None, bond_type=None, aromatic=None, sybyl=None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Indices of the atoms involved in the bond, length should be 2
        self._atom_references = atom_references
        
        # Bond type in the force field
        self._bond_type = bond_type
        
        # Indicates the bond order of this bond
        self._sybyl = sybyl
    
    @property
    def atom_references(self):

        return self._atom_references

    @property
    def bond_type(self):

        return self._bond_type

    @property
    def aromatic(self):

        return self._aromatic

    @property
    def sybyl(self):

        return self._sybyl
    
    @atom_references.setter
    def atom_references(self, value):

        self._atom_references = value

    @bond_type.setter
    def bond_type(self, value):

        self._bond_type = value

    @aromatic.setter
    def aromatic(self, value):

        self._aromatic = value

    @sybyl.setter
    def sybyl(self, value):

        self._sybyl = value

    def OnSerialize( self, logger = None ):   

        result = {}
        
        if not (self._atom_references is None):

            ser_values = []
            for item in self._atom_references:

                if isinstance(item, Atom):
                    item = item.ToReference()

                ser_values.append( item.OnSerialize(logger) )

            result["atom_references"] = ser_values
        
        if self._bond_type:

            type_str = None
            if isinstance(self._bond_type, ForceFieldReference):
                type_str = self._bond_type.key

            elif isinstance(self._bond_type, BondType):
                type_str = self._bond_type.OnSerialize(logger)
                
            else:
                print(self._bond_type)
                raise LieTopologyException("Bond::OnSerialize","Unknown bond type") 
        
            result["bond_type"] = type_str    

        
        SerializeFlatTypes( ["aromatic", "sybyl"], self.__dict__, result, '_' )

        return result

    def OnDeserialize( self, data, logger = None ):

        if "atom_references" in data:
            self._atom_references = []

            for reference in data["atom_references"]:

                if not isinstance(reference, dict):
                    raise LieTopologyException("Bond::OnDeserialize","Unknown bond reference") 
                    
                ref_obj = AtomReference()
                ref_obj.OnDeserialize(reference, logger)
                
                self._atom_references.append(ref_obj)

        if "bond_type" in data:
            localData = data["bond_type"]

            if isinstance(localData, str):
                self._bond_type = ForceFieldReference( key=localData )

            elif isinstance(localData, dict):
                self._bond_type = BondType()
                self._bond_type.OnDeserialize(localData, logger)
                
            else:
                 raise LieTopologyException("Bond::OnSerialize","Unknown bond type") 


        DeserializeFlatTypes( ["aromatic", "sybyl"], data, self.__dict__, '_' )
    
    
    def _DebugRef(self, atom_ref):

        response = "?"

        if isinstance(atom_ref, Atom):
            response = atom_ref.ToReference().Debug()
        else:
            # mark as not yet resolved
            response = "%s*" % (  atom_ref. Debug() )
        
        return response

    def Debug(self):

        safe_ref_1 = "?"
        safe_ref_2 = "?"
        safe_bond_type = "?"
        safe_sybyl = self._sybyl if self._sybyl is not None else "?"

        if self._atom_references and len(self._atom_references) == 2:
            safe_ref_1 = self._DebugRef( self._atom_references[0] )
            safe_ref_2 = self._DebugRef( self._atom_references[1] )

        if self._bond_type:
            if isinstance(self._bond_type, BondType):
                safe_bond_type = "%s" % (self._bond_type.key)
            else:
                safe_bond_type = "%s*" % (self._bond_type.key)

        # Indicates the bond order of this bond
        return "bond %-25s %-25s %7s %7s\n" % (safe_ref_1, safe_ref_2, safe_bond_type, safe_sybyl)
        