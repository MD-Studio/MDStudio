import uid

from collections import OrderedDict

from lie_topology.core.atom import Atom

class Molecule(object):

    def __init__(self, uid):

        self._uid = uid

        self._atoms = OrderedDict()

    @property 
    def uid(self):
        return self._uid

    @property
    def atoms(self):
        for atom in self._atoms.items():
            yield atom 

    def add_atom(self):

        uid = uuid.uuid4()
        atom = Atom(uid=uid)
        self._atoms[uid] = atom

        return atom