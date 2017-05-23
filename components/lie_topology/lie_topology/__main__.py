
import json
import yaml

from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.mtbParser import ParseMtb
from lie_topology.parsers.cnfParser import ParseCnf
from lie_topology.parsers.ifpParser import ParseIfp
from lie_topology.parsers.pdbParser import ParsePdb

from lie_topology.writers.cnfWriter import WriteCnf

from lie_topology.molecule.crystal import BoxVectorsToLattice, LatticeToBoxVectors


def main():

    with open( "../tests/data/pdb/peptide.pdb", 'r') as ifstream:    
        
        pdb_structures = ParsePdb( ifstream )
        
        with open( "../tests/data/cnf/test_write.cnf", 'w') as ofstream:
            
            WriteCnf( ofstream, pdb_structures )
    
    with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:

        cnf_structures = ParseCnf( ifstream )

        with open( "../tests/data/cnf/test_write2.cnf", 'w') as ofstream:
            
            WriteCnf( ofstream, cnf_structures )
    
    #v1(x)     v2(y)     v3(z)     v1(y)     v1(z)     v2(x)     v2(z)    v3(x)     v3(y)
    #7.52775   7.52775   5.32290   0.00000   0.00000   0.00000   0.00000   3.76386   3.76386
    v1 = [ 7.52775, 0.0, 0.0 ]
    v2 = [ 0.00000, 7.52775, 0.00000 ]
    v3 = [ 3.76386, 3.76386, 5.32290 ]

    test_lattice = BoxVectorsToLattice( v1, v2, v3 )

    print v1
    print v2
    print v3
    print( "CONV" )
    print test_lattice.edge_lenghts
    print test_lattice.edge_angles
    print( "CONV" )

    lattice_vectors = LatticeToBoxVectors( test_lattice )
    print lattice_vectors[0]
    print lattice_vectors[1]
    print lattice_vectors[2]

    # with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:
        
    #      structures = ParseCnf( ifstream )
    	
    #      for struct in structures:
            
    #          structCpy = Structure()
    #          structCpy.OnDeserialize( struct.OnSerialize() )
            
    #          print json.dumps( structCpy.topology.OnSerialize(), indent=2 )

    # with open( "../tests/data/mtb/minimal.pept.mtb", 'r') as ifstream:    
        
    #     mtb_file = ParseMtb( ifstream )
    #     debug1 = mtb_file.OnSerialize()
    #     debug2 = BuildingBlock()
    #     debug2.OnDeserialize( debug1 )
    #     print yaml.dump( debug2.OnSerialize(), indent=2 )


    # with open( "../tests/data/ifp/2016H66.ifp", 'r') as ifstream:    
        
    #       ifp_file = ParseIfp( ifstream )

    # with open( "../tests/data/pdb/peptide.pdb", 'r') as ifstream:    
        
    #       pdb_file = ParsePdb( ifstream )


if __name__ == '__main__':

    main()