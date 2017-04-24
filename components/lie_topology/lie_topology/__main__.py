
import json

from lie_topology.molecule.atom import Atom
from lie_topology.molecule.solute import Solute
from lie_topology.parsers.cnfParser import ParseCnf
def main1():
    	
    atom = Atom()

    solute = Solute()
    solute.atoms.insert( "CA", atom )
    
    solute2 = Solute()
    solute2.OnDeserialize( solute.OnSerialize()  ); 

    print json.dumps( solute2.OnSerialize(), sort_keys=True, indent=4, separators=(',', ': ') ); 

def main2():
    
    with open( "../tests/data/cnf/md_fX_apixaban_1.cnf", 'r') as ifstream:
        
        structures = ParseCnf( ifstream );
    	
        print( structures );
        
if __name__ == '__main__':

    main1();
    main2();