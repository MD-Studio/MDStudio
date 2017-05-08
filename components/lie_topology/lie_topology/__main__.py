
import json
import yaml

from lie_topology.molecule.atom import Atom
from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.cnfParser import ParseCnf
from lie_topology.parsers.mtbParser import ParseMtb

def main():
    
    # with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:
        
    #     structures = ParseCnf( ifstream )
    	
    #     for struct in structures:
            
    #         structCpy = Structure()
    #         structCpy.OnDeserialize( struct.OnSerialize() )
            
    #         print json.dumps( structCpy.topology.OnSerialize(), indent=2 )

    with open( "../tests/data/mtb/2016H66_pept.mtb", 'r') as ifstream:    
        
        mtb_file = ParseMtb( ifstream )

if __name__ == '__main__':

    main()