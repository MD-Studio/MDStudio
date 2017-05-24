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
import numpy as np

from copy import deepcopy

from lie_topology.common.exception   import LieTopologyException
from lie_topology.common.constants   import ANGSTROM_TO_NM
from lie_topology.molecule.structure import Structure
from lie_topology.molecule.topology  import Topology
from lie_topology.molecule.bond      import Bond

def ParseMol2( ifstream ):
    
    # Gro files contain a single structure 
    # and a single nameless group
    structures = []
    structure = Structure( topology=Topology(), description="")
    structure.topology.AddGroup( key=' ', chain_id=' ' )
    structure_group = structure.topology.groups.back() 
    structure_group.AddMolecule( key="MOL", type_name="MOL", identifier=1 )
    structure_molecule = structure_group.molecules.back()

    coords = []

    ## Uses occurance map to be order agnostic
    for line in ifstream:
        if len(line.strip()) == 0:
            continue
        


    return structures