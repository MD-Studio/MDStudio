import uid

from collections import OrderedDict

from lie_topology.core.atom import Atom

class Molecule(object):

    def __init__(self, uid, name = None):

        self._uid = uid

        self._name = name

        self._atoms = OrderedDict()

        self._bonds = list()

        self._angles = list()

        self._dihedrals = list()

        self._impropers = list()

        self._exlcusions = set()

    @property 
    def uid(self):
        return self._uid

    @property 
    def name(self):
        return self._name

    @property 
    def bonds(self):
        return self._bonds

    @property 
    def angles(self):
        return self._angles 

    @property 
    def dihedrals(self):
        return self._dihedrals

    @property 
    def impropers(self):
        return self._impropers

    @property 
    def exlcusions(self):
        return self._exlcusions

    @property
    def atoms(self):
        for atom in self._atoms.items():
            yield atom 

    @name.setter
    def name(self, val):
        self._name = val 

    def add_bond(self, bond):
        self._bonds.append(bond)

    def add_angle(self, angle):
        self._angles.append(angle)

    def add_dihedral(self, dihedral):
        self._dihedrals.append(dihedral)

    def add_improper(self, improper):
        self._impropers.append(improper)

    def add_exlcusion(self, exlcusion):
        self._exlcusions.append(exlcusion)

    def add_atom(self):
        uid = uuid.uuid4()
        atom = Atom(uid=uid)
        self._atoms[uid] = atom

        return atom