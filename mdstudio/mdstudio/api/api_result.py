class APIResult(dict):
    def __init__(self, result=None, error=None, warning=None, expired=None):
        super(APIResult, self).__init__()

        if result is not None:
            self['result'] = result

        if error is not None:
            self['error'] = error

        if warning is not None:
            self['warning'] = warning

        if expired is not None:
            self['expired'] = expired

    @property
    def result(self):
        return self['result']

    @property
    def error(self):
        return self['error']

    @property
    def warning(self):
        return self['warning']

    @property
    def expired(self):
        return self['expired']
