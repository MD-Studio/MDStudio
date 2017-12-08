class APIResult(dict):
    def __init__(self, data=None, error=None, warning=None, expired=None):
        super(APIResult, self).__init__()

        if data is not None:
            self['data'] = data

        if error is not None:
            self['error'] = error

        if warning is not None:
            self['warning'] = warning

        if expired is not None:
            self['expired'] = expired

    @property
    def data(self):
        return self['data']

    @property
    def error(self):
        return self['error']

    @property
    def warning(self):
        return self['warning']

    @property
    def expired(self):
        return self['expired']
