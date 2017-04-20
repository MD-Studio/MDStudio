from lie_topology.molecule.atom import Atom

def main():
    	
    atom = Atom();
    atom.OnDeserialize( { "name" : "ttt" } );
    
    print atom.OnSerialize();

if __name__ == '__main__':

    main();