import uid

from collections import OrderedDict

from lie_topology.core.group import Group

class System(object):

    def __init__(self, uid):

        self._uid = uid

        self._groups = OrderedDict()

    @property 
    def uid(self):
        return self._uid

    @property
    def groups(self):
        for group in self._groups.items():
            yield group 

    def add_group(self):

        uid = uuid.uuid4()
        group = Group(uid=uid)
        self._groups[uid] = group

        return group