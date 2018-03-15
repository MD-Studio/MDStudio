import uid

from collections import OrderedDict

from lie_topology.core.molecule import Molecule

class Group(object):

    def __init__(self, uid, name = None):

        self._uid = uid

        self._name = name

        self._molecules = OrderedDict()

    @property 
    def uid(self):
        return self._uid

    @property 
    def name(self):
        return self._name

    @property
    def molecules(self):
        for molecule in self._molecules.items():
            yield molecule 

    @name.setter
    def name(self, val):
        self._name = name 

    def add_molecule(self):

        uid = uuid.uuid4()
        molecule = Molecule(uid=uid)
        self._molecules[uid] = molecule

        return molecule