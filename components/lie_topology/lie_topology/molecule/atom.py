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

from copy import deepcopy

from lie_topology.common.serializable import Serializable
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.reference import AtomReference

from enum import Enum

class AtomStatus(Enum):
    default   = 1
    trailing  = 2
    preceding = 3
    replacing = 4

    @staticmethod
    def StringToEnum( x ):
        return {
        'default'   : AtomStatus.default,
        'trailing'  : AtomStatus.trailing,
        'preceding' : AtomStatus.preceding,
        'replacing' : AtomStatus.replacing,
        }.get(x, None)
    
    @staticmethod
    def EnumToString( x ):
        return {
        AtomStatus.default   : 'default',
        AtomStatus.trailing  : 'trailing',
        AtomStatus.preceding : 'preceding',
        AtomStatus.replacing : 'replacing',
        }.get(x, None)

class Atom( Serializable ):
    
    def __init__( self, parent = None, key = None, type_name = None, element = None, identifier = None,\
                  sybyl = None, occupancy = None, b_factor = None, mass_type = None, vdw_type = None,\
                  charge = None, coulombic_type = None, charge_group = None, virtual_site = None,\
                  status = AtomStatus.default ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        self._IgnoreCategory("molecule")

        # parent molecule
        self.molecule = parent

        # key of the atom
        self._key = key
        
        # actual name of the atom type
        self.type_name = type_name

        # Element of the atom
        self.element = element
        
        # Identifier number defined by external sources
        self.identifier = identifier
        
        # Indicates if this atom is part of an aromatic system
        self.sybyl = sybyl
        
        # If from a crystallographic source store the occupancy
        self.occupancy = occupancy

        # If from a crystallographic source store the bfactor
        self.b_factor = b_factor

        # Mass type, to be combined with a force field input
        self.mass_type = mass_type
        
        # Van der waals type, to be combined with a force field input
        self.vdw_type = vdw_type
        
        # direct charge assignment, other option is coulombic type
        # if charge is NOT none, it is assumed as an override for the type
        self.charge = charge

        # Coulombic type, to be combined with a force field input
        self.coulombic_type = coulombic_type
        
        # Charge group indiciation
        self.charge_group = charge_group
        
        # Virtual site treatment
        self.virtual_site = virtual_site

        # Signal atom status
        self.status = status

    @property
    def key(self):

        return self._key


    @property
    def internal_index(self):

        index=0
        if self.molecule:

            # fetch the local index (within molecule)
            index=self.molecule.IndexOfAtom(self.key)

            # then offset by atomstart of this molecule
        return index

    def SafeCopy(self, key=None):

        if key is None:
            key = self.key

        vdw_type_cpy = None
        mass_type_cpy = None
        virtual_site_cpy = None
        coulombic_type_cpy = None
        
        if self.vdw_type:
            vdw_type_cpy = deepcopy(self.vdw_type)
        
        if self.mass_type:
            mass_type_cpy = deepcopy(self.mass_type)

        if self.coulombic_type:
            coulombic_type_cpy = deepcopy(self.coulombic_type)
        
        if self.virtual_site:
            virtual_site_cpy = _CopyVsite(self.virtual_site, rename_dict )

        return Atom( key=key, type_name=self.type_name, element=self.element,\
                     identifier=self.identifier, sybyl=self.sybyl,\
                     mass_type=mass_type_cpy, vdw_type=vdw_type_cpy,\
                     coulombic_type=coulombic_type_cpy, charge=self.charge, charge_group=self.charge_group,\
                     virtual_site=virtual_site_cpy, status=self.status )


    def ToReference(self):

        atom_key=self.key
        molecule_key=None
        group_key=None
        
        molecule = self.molecule
        if molecule:
            molecule_key=molecule.key

            group = molecule.group
            if group:
                group_key=group.key
        
        return AtomReference( atom_key=atom_key,molecule_key=molecule_key,group_key=group_key )
    
    def Debug(self):
        
        # key of the atom
        key        = str(self.key) if self.key is not None else "?"
        type_name  = str(self.type_name) if self.type_name is not None else "?"
        element    = str(self.element) if self.element is not None else "?"
        identifier = str(self.identifier) if self.identifier is not None else "?"
        sybyl      = str(self.sybyl) if self.sybyl is not None else "?"

        return "atom %7s %7s %7s %7s %7s\n" % (key, type_name, element, identifier, sybyl)