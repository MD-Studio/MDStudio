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

import sys
import os
import yaml
import numpy as np

from lie_topology.common.util             import ordered_load
from lie_topology.common.exception        import LieTopologyException
from lie_topology.forcefield.forcefield   import *

def ParseMeta( forcefield, meta_stream  ):

    if not "forcefield" in meta_stream:
        raise LieTopologyException("ParseMeta", "Meta requires a forcefield section")

    if not "version" in meta_stream:
        raise LieTopologyException("ParseMeta", "Meta requires a version section")

    forcefield.key = meta_stream["forcefield"]
    forcefield.description = meta_stream["version"]

def ParseHeader( forcefield, stream ):

    if not "meta" in stream:
        raise LieTopologyException("ParseHeader", "MdTop requires a meta section")

    if not "linkexclusions" in stream:
        raise LieTopologyException("ParseHeader", "MdTop requires a linkexclusions section")
    
    ParseMeta( forcefield, stream["meta"] )

    forcefield.linkexclusions = stream["linkexclusions"]

def ParseMassTypes( forcefield, stream ):

    if not "mass_types" in stream:
        raise LieTopologyException("ParseMassTypes", "MdTop requires a mass_types section")

    mass_stream = stream["mass_types"]

    for type_code, masstype_data in mass_stream.items():

        massType = MassType( key=type_code, mass=masstype_data, type_name=type_code )
        forcefield.masstypes.insert( type_code, massType )

def ParseAtomTypes( forcefield, stream ):

    if not "atom_types" in stream:
        raise LieTopologyException("ParseAtomTypes", "MdTop requires a atom_types section")

    atom_stream = stream["atom_types"]

    for type_code, atomtype_data in atom_stream.items():

        if not "c6_sqrt" in atomtype_data:
            raise LieTopologyException("ParseAtomTypes", "AtomType requires a c6_sqrt section")

        if not "c12_sqrt" in atomtype_data:
            raise LieTopologyException("ParseAtomTypes", "AtomType requires a c12_sqrt section")

        if not "c6_1-4_sqrt" in atomtype_data:
            raise LieTopologyException("ParseAtomTypes", "AtomType requires a c6_1-4_sqrt section")

        if not "c12_1-4_sqrt" in atomtype_data:
            raise LieTopologyException("ParseAtomTypes", "AtomType requires a c12_1-4_sqrt section")

        c6_sqrt     = atomtype_data["c6_sqrt"]
        c12_sqrt    = atomtype_data["c12_sqrt"]
        c6_14_sqrt  = atomtype_data["c6_1-4_sqrt"]
        c12_14_sqrt = atomtype_data["c12_1-4_sqrt"]

        vdw_type = VdwType( key=type_code, type_name=type_code, c6_sqrt=c6_sqrt, c6_14_sqrt=c6_14_sqrt,\
                            c12_sqrt=c12_sqrt, c12_14_sqrt=c12_14_sqrt  )

        forcefield.vdwtypes.insert( type_code,  vdw_type )

def ParsePairInteractions( forcefield, stream ):

    if not "pair_interactions" in stream:
        raise LieTopologyException("ParsePairInteractions", "MdTop requires a pair_interactions section")

    inter_pair_stream = stream["pair_interactions"]

    for type_code, matrix_data in inter_pair_stream.items():

        vdw_type = forcefield.vdwtypes[type_code]
        vdw_type.matrix = dict()

        for matrix_key, matrix_entry in matrix_data.items():

            # we encode them as 1-3 to stay in line with GROMOS
            matrix_entry = matrix_entry - 1

            if matrix_entry <= 0 or matrix_entry > 2:
                raise LieTopologyException("ParsePairInteractions", "Off diagional matrix elements need to point to c12 element 1-3")

            vdw_type.matrix[matrix_key] = matrix_entry

def ParseVdwMixedInteractions( forcefield, stream ):

    if not "vdw_mixed" in stream:
        raise LieTopologyException("ParsePairInteractions", "MdTop requires a vdw_mixed section")

    vdw_mixed = stream["vdw_mixed"]

    for pair_key, pair_data in vdw_mixed.items():
        
        # start by disecting the key
        parts = pair_key.split("::")

        if len(parts) != 2:
            raise LieTopologyException("ParseVdwMixedInteractions", "A mixed vdw type requires two valid vdw types in the key seperated by '::'")

        if not "c6" in pair_data or\
           not "c12" in pair_data or\
           not "c6_1-4" in pair_data or\
           not "c12_1-4" in pair_data:

           raise LieTopologyException("ParseVdwMixedInteractions", "A mixed vdw type requires a c6, c12, c6_1-4 and c12_1-4 entry")

        c6     = pair_data["c6"]
        c12    = pair_data["c12"]
        c6_14  = pair_data["c6_1-4"]
        c12_14 = pair_data["c12_1-4"]
        
        if not parts[0] in forcefield.vdwtypes:
            raise LieTopologyException("ParsePairInteractions", "%s is not a valid vdw type" % (parts[0]) )

        if not parts[1] in forcefield.vdwtypes:
            raise LieTopologyException("ParsePairInteractions", "%s is not a valid vdw type" % (parts[1]) )

        mixed = VdwMixed( references=parts, c6=c6, c12=c12, c6_14=c6_14, c12_14=c12_14 )
        forcefield.vdwmixed.insert( pair_key, mixed ) 

def ParseCoulombicTypes( forcefield, stream ):

    if not "coulombic_types" in stream:
        raise LieTopologyException("ParsePairInteractions", "MdTop requires a coulombic_types section")

    coulombic_types = stream["coulombic_types"]

    for coulomb_key, coulomb_data in coulombic_types.items():
        
        if not "charge" in coulomb_data or\
           not "cos-charge" in coulomb_data or\
           not "damping-level" in coulomb_data or\
           not "damping-power" in coulomb_data or\
           not "polarizability" in coulomb_data:

           raise LieTopologyException("ParseCoulombicTypes", "A coulombic type requires a charge, cos-charge, damping-level, damping-power and polarizability entry") 

        charge = coulomb_data["charge"]
        cos_charge = coulomb_data["cos-charge"]
        damping_level = coulomb_data["damping-level"]
        damping_power = coulomb_data["damping-power"]
        polarizability = coulomb_data["polarizability"]

        coultype = CoulombicType( key = coulomb_key, charge =charge, polarizability = polarizability, cos_charge = cos_charge,\
                                  damping_level = damping_level, damping_power = damping_power  )

        forcefield.coultypes.insert( coulomb_key, coultype ) 

def ParseBondTypes( forcefield, stream ):

    if not "bond_types" in stream:
        raise LieTopologyException("ParseBondTypes", "MdTop requires a bond_types section")
    
    bond_types = stream["bond_types"]

    for bond_key, bond_data in bond_types.items():

        if not "fc-quartic" in bond_data or\
           not "fc-harmonic" in bond_data or\
           not "bond0" in bond_data:

           raise LieTopologyException("ParseBondTypes", "A bond type requires a fc-quartic, fc-harmonic and bond0 entry") 

        fc_quartic  = bond_data["fc-quartic"]
        fc_harmonic = bond_data["fc-harmonic"]
        bond0       = bond_data["bond0"]
        
        bond = BondType( key=bond_key, fc_quartic=fc_quartic, fc_harmonic=fc_harmonic, bond0=bond0)
        forcefield.bondtypes.insert( bond_key, bond )

def ParseAngleTypes( forcefield, stream ):

    if not "angle_types" in stream:
        raise LieTopologyException("ParseAngleTypes", "MdTop requires a angle_types section")
    
    angle_types = stream["angle_types"]

    for angle_key, angle_data in angle_types.items():

        if not "fc-non-harmonic" in angle_data or\
           not "fc-harmonic" in angle_data or\
           not "angle0" in angle_data:

           raise LieTopologyException("ParseAngleTypes", "An angle type requires a fc-non-harmonic, fc-harmonic and angle0 entry") 

        fc_cos_harmonic = angle_data["fc-non-harmonic"]
        fc_harmonic     = angle_data["fc-harmonic"]
        angle0          = angle_data["angle0"]

        angle = AngleType( key=angle_key, fc_cos_harmonic=fc_cos_harmonic, fc_harmonic=fc_harmonic, angle0=angle0 ) 
        forcefield.angletypes.insert( angle_key,  angle )

def ParseDihedralTypes( forcefield, stream ):

    if not "dihedral_types" in stream:
        raise LieTopologyException("ParseDihedralTypes", "MdTop requires a dihedral_types section")
    
    dihedral_types = stream["dihedral_types"]

    for dihedral_key, dihedral_data in dihedral_types.items():

        if not "fc" in dihedral_data or\
           not "phase-shift" in dihedral_data or\
           not "multiplicity" in dihedral_data:

           raise LieTopologyException("ParseDihedralTypes", "A dihedral type requires a fc, phase-shift and multiplicity entry") 

        force_constant = dihedral_data["fc"]
        phaseShift     = dihedral_data["phase-shift"]
        multiplicity   = dihedral_data["multiplicity"]
        
        dihedral = DihedralType(key=dihedral_key, force_constant=force_constant, phaseShift=phaseShift, multiplicity=multiplicity)
        forcefield.dihedraltypes.insert( dihedral_key,  dihedral )

def ParseImproperTypes( forcefield, stream ):

    if not "improper_types" in stream:
        raise LieTopologyException("ParseImproperTypes", "MdTop requires a improper_types section")
    
    improper_types = stream["improper_types"]

    for improper_key, improper_data in improper_types.items():

        if not "fc" in improper_data or\
           not "angle0" in improper_data:

           raise LieTopologyException("ParseImproperTypes", "A improper type requires a fc and angle0 entry") 

        force_constant = improper_data["fc"]
        angle0         = improper_data["angle0"]
        
        improper = ImproperType(key=improper_key, force_constant=force_constant, angle0=angle0 )
        forcefield.impropertypes.insert( improper_key,  improper )

def ParseMdtop( ifstream ):

    forcefield = ForceField()

    stream = ordered_load( ifstream )
    ParseHeader( forcefield, stream )
    ParseMassTypes( forcefield, stream )
    ParseAtomTypes( forcefield, stream )
    ParsePairInteractions( forcefield, stream )
    ParseVdwMixedInteractions( forcefield, stream )
    ParseCoulombicTypes( forcefield, stream )
    ParseBondTypes( forcefield, stream )
    ParseAngleTypes( forcefield, stream )
    ParseDihedralTypes( forcefield, stream )
    ParseImproperTypes( forcefield, stream )

    return forcefield