from twisted.logger import Logger as _Logger

class Logger(_Logger):
    def __init__(self, namespace=None):
        super(Logger, self).__init__(namespace=namespace)
