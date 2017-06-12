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

from lie_topology.common.serializable import Serializable
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.atom import Atom
from lie_topology.molecule.reference import AtomReference
from lie_topology.forcefield.forcefield import AngleType
from lie_topology.forcefield.reference import ForceFieldReference

class Angle( Serializable ):
    
    def __init__( self, atom_references = None, angle_type = None, united = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

        # Indices of the atoms involved in the angle, length should be 3
        self._atom_references = atom_references
        
        # Angle type in the force field
        self._angle_type = angle_type
    
    @property
    def atom_references(self):

        return self._atom_references

    @property
    def angle_type(self):

        return self._angle_type

    @atom_references.setter
    def atom_references(self, value):

        self._atom_references = value

    def OnSerialize( self, logger = None ):   

        result = {}
        
        if not (self._atom_references is None):

            ser_values = []
            for item in self._atom_references:

                if isinstance(item, Atom):
                    item = item.ToReference()

                ser_values.append( item.OnSerialize(logger) )

            result["atom_references"] = ser_values
        
        if self._angle_type:

            type_str = None
            if isinstance(self._angle_type, ForceFieldReference):
                type_str = self._angle_type.key

            elif isinstance(self._angle_type, AngleType):
                type_str = self._angle_type.OnSerialize(logger)
                
            else:
                print(self._angle_type)
                raise LieTopologyException("Angle::OnSerialize","Unknown angle type") 
        
            result["angle_type"] = type_str    

        return result
    
    def OnDeserialize( self, data, logger = None ):

        if "atom_references" in data:
            self._atom_references = []

            for reference in data["atom_references"]:

                if not isinstance(reference, dict):
                    raise LieTopologyException("Angle::OnDeserialize","Unknown angle reference") 
                    
                ref_obj = AtomReference()
                ref_obj.OnDeserialize(reference, logger)
                
                self._atom_references.append(ref_obj)
                
        if "angle_type" in data:
            localData = data["angle_type"]

            if isinstance(localData, str):
                self._angle_type = ForceFieldReference( key=localData )

            elif isinstance(localData, dict):
                self._angle_type = AngleType()
                self._angle_type.OnDeserialize(localData, logger)
                
            else:
                 raise LieTopologyException("Angle::OnSerialize","Unknown angle type") 
    
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
        safe_ref_3 = "?"
        safe_angle_type = "?"

        if self._atom_references and len(self._atom_references) == 3:
            safe_ref_1 = self._DebugRef( self._atom_references[0] )
            safe_ref_2 = self._DebugRef( self._atom_references[1] )
            safe_ref_3 = self._DebugRef( self._atom_references[2] )

        if self._angle_type:
            if isinstance(self._angle_type, AngleType):
                safe_angle_type = "%s" % (self._angle_type.key)
            else:
                safe_angle_type = "%s*" % (self._angle_type.key)

        # Indicates the bond order of this bond
        return "angle %-25s %-25s %-25s %7s\n" % (safe_ref_1, safe_ref_2, safe_ref_3, safe_angle_type)