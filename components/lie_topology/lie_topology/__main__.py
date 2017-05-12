
import json
import yaml

from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.buildingBlock import BuildingBlock
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.mtbParser import ParseMtb
from lie_topology.parsers.cnfParser import ParseCnf
from lie_topology.parsers.ifpParser import ParseIfp
from lie_topology.parsers.pdbParser import ParsePdb

def main():
    
    # with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:
        
    #     structures = ParseCnf( ifstream )
    	
    #     for struct in structures:
            
    #         structCpy = Structure()
    #         structCpy.OnDeserialize( struct.OnSerialize() )
            
    #         print json.dumps( structCpy.topology.OnSerialize(), indent=2 )

    with open( "../tests/data/mtb/minimal.pept.mtb", 'r') as ifstream:    
        
        mtb_file = ParseMtb( ifstream )
        debug1 = mtb_file.OnSerialize()
        debug2 = BuildingBlock()
        debug2.OnDeserialize( debug1 )
        print yaml.dump( debug2.OnSerialize(), indent=2 )


    # with open( "../tests/data/ifp/2016H66.ifp", 'r') as ifstream:    
        
    #      ifp_file = ParseIfp( ifstream )

    # with open( "../tests/data/pdb/peptide.pdb", 'r') as ifstream:    
        
    #      pdb_file = ParsePdb( ifstream )


if __name__ == '__main__':

    main()