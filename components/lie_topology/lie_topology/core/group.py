import uid

from collections import OrderedDict

from lie_topology.core.molecule import Molecule

class Group(object):

    def __init__(self, uid):

        self._uid = uid

        self._molecules = OrderedDict()

    @property 
    def uid(self):
        return self._uid

    @property
    def molecules(self):
        for molecule in self._molecules.items():
            yield molecule 

    def add_molecule(self):

        uid = uuid.uuid4()
        molecule = Molecule(uid=uid)
        self._molecules[uid] = molecule

        return molecule