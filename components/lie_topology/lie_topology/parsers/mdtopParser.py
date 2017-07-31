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

from lie_topology.common.exception        import LieTopologyException
from lie_topology.forcefield.forcefield   import *


def ParseMeta( forcefield, meta_stream  ):

    if not "forcefield" in meta_stream:
        raise LieTopologyException("ParseMeta", "Meta requires a forcefield section")

    if not "version" in meta_stream:
        raise LieTopologyException("ParseMeta", "Meta requires a version section")

    forcefield.key = meta_stream["forcefield"]
    forcefield.description = meta_stream["version"]

    print (forcefield.description)

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


def ParseMdtop( ifstream ):

    forcefield = ForceField()

    stream = yaml.load(ifstream)
    ParseHeader( forcefield, stream )
    ParseMassTypes( forcefield, stream )
    ParseAtomTypes( forcefield, stream )



    return forcefield