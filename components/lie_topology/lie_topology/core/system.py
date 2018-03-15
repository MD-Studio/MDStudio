import uid

from collections import OrderedDict

from lie_topology.core.group import Group
from lie_topology.core.uuid import UUIDGenerator

class System(object):

    def __init__(self):

        self._signature = uuid.uuid4()

        self._atom_uuid     = UUIDGenerator()
        self._molecule_uuid = UUIDGenerator()
        self._group_uuid    = UUIDGenerator()


        self._groups = OrderedDict()

    @property 
    def uid(self):
        return self._uid

    @property
    def groups(self):
        for group in self._groups.items():
            yield group 

    def add_group(self):

        uid 
        group = Group(uid=uid)
        self._groups[uid] = group

        return group