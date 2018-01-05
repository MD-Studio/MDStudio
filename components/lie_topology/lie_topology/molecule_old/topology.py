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
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException
from lie_topology.molecule.group import Group 
from lie_topology.molecule.molecule import Molecule

from lie_topology.forcefield.forcefield import ForceField
from lie_topology.forcefield.reference import ForceFieldReference

class Topology( Serializable ):
    
    def __init__( self, solvent = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__( self, self.__module__, self.__class__.__name__ )
        
        # Solutes present in this topology
        self._groups = ContiguousMap()

        # Solvent present in this topology
        self._solvent = solvent

    def atomByIndex(self, index):
        
        # could be speed up a lot by storing a linear version of the topology
        # for now if its fast enough there is not reason to do this
        it = 0
        for group in self._groups.values():
            for molecule in group.molecules.values():

                numAtoms = len(molecule.atoms)
                
                if index >= it and index < ( it + numAtoms):
                    return molecule.atoms.at( index - it )
                
                it += numAtoms

        return None
    
    def AtomIndexStartOfGroup(self, group_key):

        index_start=0
        
        for group in self._groups.values():

            if group.key == group_key:
                break
            
            index_start+=group.atom_count

        return index_start

    @property
    def atom_count(self):

        count = 0
        for group in self._groups.values():
            count += group.atom_count
        
        return count

    @property
    def solvent_atom_count(self):

        if self._solvent is not None:
            return self._solvent.atom_count

        else:
            return 0

    @property
    def groups(self):

        return self._groups

    @property
    def solvent(self):

        return self._solvent

    def AddGroup( self, **kwargs ):

        if not "key" in kwargs:

            raise LieTopologyException("Topology::AddGroup", "key is a required argument" )
        
        kwargs["parent"] = self
        self._groups.insert( kwargs["key"], Group( **kwargs ) )

    def GroupByKey( self, key ):

        return self._groups[key]
    
    def _ResolveAtomForceFieldReference(self, molecule, forcefield):

        for atom_key, atom in molecule.atoms.items():

            vdw_type       = atom.vdw_type
            mass_type      = atom.mass_type
            coulombic_type = atom.coulombic_type
            
            # all of the force field types could be references
            if vdw_type is not None and isinstance( vdw_type, ForceFieldReference):
                if not vdw_type.key in forcefield.vdwtypes:
                    raise LieTopologyException("Topology::_ResolveAtomForceFieldReference",\
                                               "Vdw_type %s not found in forcefield"\
                                                % ( vdw_type.key ) ) 
                atom.vdw_type = forcefield.vdwtypes.find(vdw_type.key)
            
            if mass_type is not None and isinstance( mass_type, ForceFieldReference):
                if not mass_type.key in forcefield.masstypes:
                    raise LieTopologyException("Topology::_ResolveAtomForceFieldReference",\
                                               "Mass_type %s not found in forcefield"\
                                                % ( mass_type.key ) ) 
                atom.mass_type = forcefield.masstypes.find(mass_type.key)
            
            if coulombic_type is not None and isinstance( coulombic_type, ForceFieldReference):
                if not coulombic_type.key in forcefield.coultypes:
                    raise LieTopologyException("Topology::_ResolveAtomForceFieldReference",\
                                               "Coul_type %s not found in forcefield"\
                                                % ( coulombic_type.key ) ) 
                atom.coulombic_type = forcefield.coultypes.find(coulombic_type.key)
    
    def _ResolveBondedForceFieldReference( self, bonded_list, bonded_types ):

        for bonded in bonded_list:

            forcefield_type = bonded.forcefield_type

            # all of the force field types could be references
            if forcefield_type is not None and isinstance( forcefield_type, ForceFieldReference):
                if not forcefield_type.key in bonded_types:
                    raise LieTopologyException("Topology::_ResolveBondedForceFieldReference",\
                                               "forcefield_type %s not found in forcefield"\
                                                % ( forcefield_type.key ) ) 
                bonded.forcefield_type = bonded_types.find(forcefield_type.key)


    def ResolveForceFieldReferences( self, forcefield ):

        if not isinstance(forcefield, ForceField):
            raise LieTopologyException( "Topology::ResolveForceFieldReferences", "Forcefield input is not of type ForceField" )

        ##
        ## Resolve all references of type ForceFieldReference
        ##

        for group_key, group in self.groups.items():
            for molecule_key, molecule in group.molecules.items():

                 self._ResolveAtomForceFieldReference(molecule, forcefield)
                 self._ResolveBondedForceFieldReference( molecule.bonds, forcefield.bondtypes )
                 self._ResolveBondedForceFieldReference( molecule.angles, forcefield.angletypes )
                 self._ResolveBondedForceFieldReference( molecule.dihedrals, forcefield.dihedraltypes )
                 self._ResolveBondedForceFieldReference( molecule.impropers, forcefield.impropertypes )

    def OnSerialize( self, logger = None ):   

        result = {}
        
        SerializeContiguousMaps( ["groups"], self.__dict__, result, logger, '_' )
        SerializeObjTypes( ["solvent"], self.__dict__, result, logger, '_' )

        return result
    
    def OnDeserialize( self, data, logger = None ):

        if not IsBasicMap(data):
            raise LieTopologyException( "Topology::OnDeserialize", "Deserialize data presented is not a map" )
        
        for cat, value in data.items():
            if not self._IsValidCategory( cat ):
    	       logger.warning("Serializable::OnDeserialize category %s not valid for deserialization" % ( cat ) )
        
        DeserializeContiguousMapsTypes( ["groups"], [Group], data, self.__dict__, logger, '_', self )
        DeserializeObjTypes( ["solvent"], [Molecule], data, self.__dict__, logger, '_')
        
        # patch bonded references
        for group in self._groups.values():
            for molecule in group.molecules.values():
                molecule.ResolveReferences( self )

        if self._solvent:
            self._solvent.ResolveReferences( None )
    
    def Debug(self):

        aggregate=""
        for group in self._groups.values():

            aggregate+=group.Debug()+"\n"
        
        return aggregate

