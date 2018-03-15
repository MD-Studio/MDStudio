class UUIDGenerator(object):

    def __init__(self, base = 0):
        self._base = base

    def next(self):
        value = self._base
        self._base += 1

        return value
