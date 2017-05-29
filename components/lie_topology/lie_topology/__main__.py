
import json
import yaml

from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.mtbParser import ParseMtb
from lie_topology.parsers.cnfParser import ParseCnf
from lie_topology.parsers.ifpParser import ParseIfp
from lie_topology.parsers.pdbParser import ParsePdb
from lie_topology.parsers.groParser import ParseGro
from lie_topology.parsers.sdfParser import ParseSdf
from lie_topology.parsers.mol2Parser import ParseMol2

from lie_topology.writers.cnfWriter import WriteCnf

from lie_topology.molecule.crystal import BoxVectorsToLattice, LatticeToBoxVectors


def main():

    # with open( "../tests/data/pdb/peptide.pdb", 'r') as ifstream:    
        
    #     pdb_structures = ParsePdb( ifstream )
        
    #     with open( "../tests/data/cnf/test_write.cnf", 'w') as ofstream:
            
    #         WriteCnf( ofstream, pdb_structures )
    
    # with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:

    #     cnf_structures = ParseCnf( ifstream )

    #     with open( "../tests/data/cnf/test_write2.cnf", 'w') as ofstream:
            
    #         WriteCnf( ofstream, cnf_structures )
    
    # with open( "../tests/data/gro/run1_combined_pbc.gro", 'r') as ifstream:

    #     gro_structures = ParseGro( ifstream )

    #     with open( "../tests/data/cnf/test_write3.cnf", 'w') as ofstream:
            
    #         WriteCnf( ofstream, gro_structures )

    # with open( "../tests/data/sdf/BHC2.sdf", 'r') as ifstream:

    #     sdf_structures = ParseSdf( ifstream )

    #     with open( "../tests/data/cnf/test_write4.cnf", 'w') as ofstream:
            
    #         WriteCnf( ofstream, sdf_structures )     

    with open( "../tests/data/mol2/BHC2.mol2", 'r') as ifstream:

        mol2_structures = ParseMol2( ifstream )

        with open( "../tests/data/cnf/test_write5.cnf", 'w') as ofstream:
            
            WriteCnf( ofstream, mol2_structures )  

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