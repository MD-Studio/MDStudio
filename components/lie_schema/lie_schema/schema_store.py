from mdstudio.db.model import Model
from mdstudio.deferred.lock import Lock


class ResourceRepository:
    class Resources(Model):
        pass

    def __init__(self):
        self.repo = ResourceRepository.Resources()

    def find(self, group, component):
        return self.find_one({
            'group': group,
            'component': component
        })


class SchemaStore(object):
    def __init__(self):
        self.lock = Lock()
