"""
import json
import yaml


from lie_topology.molecule.molecule import Molecule
from lie_topology.molecule.blueprint import Blueprint
from lie_topology.molecule.structure import Structure
from lie_topology.parsers.cnfParser import ParseCnf
from lie_topology.parsers.pdbParser import ParsePdb
from lie_topology.parsers.groParser import ParseGro
from lie_topology.parsers.sdfParser import ParseSdf
from lie_topology.parsers.mol2Parser import ParseMol2
from lie_topology.parsers.mdtopParser import ParseMdtop
from lie_topology.parsers.mdmtbParser import ParseMDMtb

from lie_topology.utilities.make_topology import MakeSequence

from lie_topology.writers.cnfWriter import WriteCnf
from lie_topology.writers.gromosTopologyWriter import WriteGromosTopology

from lie_topology.forcefield.physconst import PhysicalConstants
from lie_topology.molecule.crystal import BoxVectorsToLattice, LatticeToBoxVectors


def WriteSimJson( forcefield, coordinates ):

    pass

def main():

    topology = None
    coordinates = None

    with open( "../tests/data/cnf/M01.g96", 'r') as cnf_ifs:

        structures = ParseCnf( cnf_ifs )

    with open( "../tests/data/md_top/54a7.aatop", 'r') as mdaa_ifs,\
         open( "../tests/data/md_top/54a7.mdtop", 'r') as mdtop_ifs:

        forcefield = ParseMdtop( mdtop_ifs )
        blueprint = ParseMDMtb( mdaa_ifs )

        phys_const = PhysicalConstants()

        topology = MakeSequence( forcefield, blueprint, [
                  "NH3+_THR","ILE","LYSH","GLU","MET","PRO","GLN","PRO","LYSH","THR",
                  "PHE","GLY","GLU","LEU","LYSH","ASN","LEU","PRO","LEU","LEU",
                  "ASN","THR","ASP","LYSH","PRO","VAL","GLN","ALA","LEU","MET",
                  "LYSH","ILE","ALA","ASP","GLU","LEU","GLY","GLU","ILE","PHE",
                  "LYSH","PHE","GLU","ALA","PRO","GLY","LEU","VAL","THR","ARG",
                  "TYR","LEU","SER","SER","GLN","ARG","LEU","ILE","LYSH","GLU",
                  "ALA","CYSH","ASP","GLU","SER","ARG","PHE","ASP","LYSH","ASN",
                  "LEU","ILE","GLN","ALA","LEU","LYSH","PHE","VAL","ARG","ASP",
                  "PHE","TRP","GLY","ASP","GLY","LEU","VAL","THR","SER","TRP",
                  "THR","HISA","GLU","LYSH","ASN","TRP","LYSH","LYSH","ALA","HISA",
                  "ASN","ILE","LEU","LEU","PRO","SER","PHE","SER","GLN","GLN",
                  "ALA","MET","LYSH","GLY","TYR","HISB","ALA","MET","MET","VAL",
                  "ASP","ILE","ALA","VAL","GLN","LEU","VAL","GLN","LYSH","TRP",
                  "GLU","ARG","LEU","ASN","ALA","ASP","GLU","HISA","ILE","GLU",
                  "VAL","PRO","GLU","ASP","MET","THR","ARG","LEU","THR","LEU",
                  "ASP","THR","ILE","GLY","LEU","CYSH","GLY","PHE","ASN","TYR",
                  "ARG","PHE","ASN","SER","PHE","TYR","ARG","ASP","GLN","PRO",
                  "HISB","PRO","PHE","ILE","THR","SER","MET","VAL","ARG","ALA",
                  "LEU","ASP","GLU","ALA","MET","ASN","LYSH","GLN","GLN","ARG",
                  "ALA","ASN","PRO","ASP","ASP","PRO","ALA","TYR","ASP","GLU",
                  "ASN","LYSH","ARG","GLN","PHE","GLN","GLU","ASP","ILE","LYSH",
                  "VAL","MET","ASN","ASP","LEU","VAL","ASP","LYSH","ILE","ILE",
                  "ALA","ASP","ARG","LYSH","ALA","SER","GLY","GLU","GLN","SER",
                  "ASP","ASP","LEU","LEU","THR","HISB","MET","LEU","ASN","GLY",
                  "LYSH","ASP","PRO","GLU","THR","GLY","GLU","PRO","LEU","ASP",
                  "ASP","GLU","ASN","ILE","ARG","TYR","GLN","ILE","ILE","THR",
                  "PHE","LEU","ILE","ALA","GLY","HISA","VAL","THR","THR","SER",
                  "GLY","LEU","LEU","SER","PHE","ALA","LEU","TYR","PHE","LEU",
                  "VAL","LYSH","ASN","PRO","HISA","VAL","LEU","GLN","LYSH","ALA",
                  "ALA","GLU","GLU","ALA","ALA","ARG","VAL","LEU","VAL","ASP",
                  "PRO","VAL","PRO","SER","TYR","LYSH","GLN","VAL","LYSH","GLN",
                  "LEU","LYSH","TYR","VAL","GLY","MET","VAL","LEU","ASN","GLU",
                  "ALA","LEU","ARG","LEU","TRP","PRO","THR","ALA","PRO","ALA",
                  "PHE","SER","LEU","TYR","ALA","LYSH","GLU","ASP","THR","VAL",
                  "LEU","GLY","GLY","GLU","TYR","PRO","LEU","GLU","LYSH","GLY",
                  "ASP","GLU","LEU","MET","VAL","LEU","ILE","PRO","GLN","LEU",
                  "HISA","ARG","ASP","LYSH","THR","ILE","TRP","GLY","ASP","ASP",
                  "VAL","GLU","GLU","PHE","ARG","PRO","GLU","ARG","PHE","GLU","ASN",
                  "PRO","SER","ALA","ILE","PRO","GLN","HISB","ALA","PHE","LYSH",
                  "PRO","PHE","GLY","ASN","GLY","GLN","ARG","ALA","CYSH","ILE",
                  "GLY","GLN","GLN","PHE","ALA","LEU","HISB","GLU","ALA","THR",
                  "LEU","VAL","LEU","GLY","MET","MET","LEU","LYSH","HISA","PHE",
                  "ASP","PHE","GLU","ASP","HISB","THR","ASN","TYR","GLU","LEU",
                  "ASP","ILE","LYSH","GLU","THR","LEU","THR","LEU","LYSH","PRO",
                  "GLU","GLY","PHE","VAL","VAL","LYSH","ALA","LYSH","SER","LYSH",
                  "LYSH","ILE","PRO","LEU_COO-" ], [] )

        #with open( "../tests/data/gtop/gen_poly_ala.gtop", 'w') as top_ofstream:
        #    WriteGromosTopology( top_ofstream, topology, forcefield, phys_const )


    json_top = {}
"""

#pipenv install --skip-lock --sequential

import json
import jsonschema

def main():
    
    # test atom schema
    with open("lie_topology/schemas/resources/atom.v1.json", 'r') as ifs:

        schema = json.load(ifs)

        test_atom = { "UID" : "a1", "name" : "CA"}
        print( test_atom )

        jsonschema.validate( test_atom, schema)


if __name__ == '__main__':

    main()