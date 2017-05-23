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

import numpy as np

from lie_topology.common.serializable import Serializable
from lie_topology.common.contiguousMap import ContiguousMap
from lie_topology.common.exception import LieTopologyException

class Lattice( Serializable ):
    
    def __init__( self, edge_lenghts = None, edge_angles = None, rotation = None, offset = None ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )

		# lenghts of the a,b & c edges, should be a vec3	
        self.edge_lenghts = edge_lenghts

		# angles between the box edges, should be a vec3
        self.edge_angles = edge_angles

		# box rotation, should be a vec3
        self.rotation = rotation

		# box offset, should be a vec3 
        self.offset = offset

def BoxVectorsToLattice( v1, v2, v3 ):

    if not len(v1) == 3 or\
       not len(v2) == 3 or\
       not len(v3) == 3:

       raise LieTopologyException("BoxVectorsToLattice", "Expected box vectors to be of dim 3")
    
    np_v1 = np.array(v1)
    np_v2 = np.array(v2)
    np_v3 = np.array(v3)

    a = np.sqrt(np_v1.dot(np_v1))
    b = np.sqrt(np_v2.dot(np_v2))
    c = np.sqrt(np_v3.dot(np_v3))

    alpha = np.degrees( np.arccos( np_v2.dot(np_v3) / (b * c)))
    beta  = np.degrees( np.arccos( np_v1.dot(np_v3) / (a * c))) 
    gamma = np.degrees( np.arccos( np_v1.dot(np_v2) / (a * b))) 

    return Lattice( edge_lenghts=[a, b, c], edge_angles=[alpha, beta, gamma] )

def LatticeToBoxVectors( lattice ):

    if lattice.edge_lenghts is None or\
       lattice.edge_angles is None:
       raise LieTopologyException("LatticeToBoxVectors", "Expected crystal edges and angles to be defined")

    a = lattice.edge_lenghts[0]
    b = lattice.edge_lenghts[1]
    c = lattice.edge_lenghts[2]

    alpha = np.radians( lattice.edge_angles[0] )
    beta  = np.radians( lattice.edge_angles[1] )
    gamma = np.radians( lattice.edge_angles[2] )

    phi   = 0.0
    theta = 0.0
    psi   = 0.0

    if lattice.rotation is not None:
        phi   = np.radians( lattice.rotation[0] )
        theta = np.radians( lattice.rotation[1] )
        psi   = np.radians( lattice.rotation[2] )

    cosDelta = (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / (np.sin(beta) * np.sin(gamma))
    sinDelta = np.sqrt( 1 - cosDelta * cosDelta )

    s1 = [ a, 0.0, 0.0 ]
    s2 = [ b * np.cos(gamma), b * np.sin(gamma), 0.0 ]
    s3 = [ c * np.cos(beta),  c * np.sin( beta ) * cosDelta, c * np.sin( beta ) * sinDelta ]

    # if a rotation is needed
    if phi != 0.0 or theta != 0.0 or psi != 0.0:

        # r1 = [ np.cos(theta) * np.cos(phi), np.cos(theta) * np.sin(phi), -np.sin(theta) ]
        # r2 = [ np.sin( psi ) * np.sin( theta ) * np.cos( phi ) - np.cos( psi ) * np.sin( phi ),\
        #        np.sin( psi ) * np.sin( theta ) * np.sin( phi ) + np.cos( psi ) * cp.cos( phi ),\
        #        np.sin( psi ) * np.cos( theta ) ] 
        # r3 = [ np.cos( psi ) * np.sin( theta ) * np.cos( phi ) + np.sin( psi ) * np.sin( phi ),\
        #        np.cos( psi ) * np.sin( theta ) * np.sin( phi ) - np.sin( psi ) * np.cos( phi ),\
        #        np.cos( psi ) * np.cos( theta ) ]

        # TODO
        raise LieTopologyException("BoxVectorsToLattice", "Crystal rotation currently not fully supported")

    return [s1, s2, s3]