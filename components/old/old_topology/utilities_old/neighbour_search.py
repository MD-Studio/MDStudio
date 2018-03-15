from lie_graph.graph import Graph
from lie_graph.graph_algorithms import dfs, node_neighbors

def _FindNeighbours( nid, bonded_graph ):

    return node_neighbors(bonded_graph, nid)

def FindExplicitPairs( nid, bonded_graph ):

    # 1-2
    search_list = _FindNeighbours( nid, bonded_graph )
    exclu_neighbours = set( search_list )

    # 1-3
    for sid in search_list:
        exclu_neighbours.update( _FindNeighbours( sid, bonded_graph ) )

    # 1-4
    search_list = list(exclu_neighbours)
    neighbours_1_4 = set()
    for sid in search_list:
        neighbours_1_4.update( _FindNeighbours( sid, bonded_graph ) )

    neighbours_1_4.difference_update( exclu_neighbours )

    # now find out what the gromos id's are
    exclu_atoms = set()
    neighbour_1_4_atoms = set()

    for nid_exclu in exclu_neighbours:
        exclu_atoms.add( bonded_graph.attr(nid_exclu)["data"] )
    
    for nid_1_4 in neighbours_1_4:
        neighbour_1_4_atoms.add( bonded_graph.attr(nid_1_4)["data"] )

    return exclu_atoms, neighbour_1_4_atoms


def GenerateBondedGraph( solute_group ):

    bonded_graph = Graph()
    atom_index_to_graphid = dict()

    # Stage 1 add nodes
    for mkey, molecule in solute_group.molecules.items():
        for akey, atom in molecule.atoms.items():
            aid = atom.internal_index
            internal_index = atom.internal_index
            nid = bonded_graph.add_node( internal_index )
            atom_index_to_graphid[internal_index] = nid

    # Stage 2 add edges
    for mkey, molecule in solute_group.molecules.items():
        for bond in molecule.bonds:
            nid1 = atom_index_to_graphid[ bond.atom_references[0].internal_index ]
            nid2 = atom_index_to_graphid[ bond.atom_references[1].internal_index ]

            if nid1 < nid2:
                bonded_graph.add_edge( nid1, nid2 )
            else:
                bonded_graph.add_edge( nid2, nid1 )

    return bonded_graph, atom_index_to_graphid