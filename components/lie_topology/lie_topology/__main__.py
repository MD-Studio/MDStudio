
import json
import yaml

from lie_topology.molecule.atom import Atom
from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.cnfParser import ParseCnf

def main():
    
    with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:
        
        structures = ParseCnf( ifstream )
    	
        for struct in structures:
            
            structCpy = Structure()
            structCpy.OnDeserialize( struct.OnSerialize() )
            
            print json.dumps( structCpy.topology.OnSerialize(), indent=2 )

        
if __name__ == '__main__':

    main()