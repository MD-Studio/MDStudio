
import json

from lie_topology.molecule.atom import Atom
from lie_topology.molecule.solute import Solute

def main():
    	
    atom = Atom()

    solute = Solute()
    solute.atoms.insert( "CA", atom )
    
    solute2 = Solute()
    solute2.OnDeserialize( solute.OnSerialize()  ); 

    print json.dumps( solute2.OnSerialize(), sort_keys=True, indent=4, separators=(',', ': ') ); 
 
if __name__ == '__main__':

    main();