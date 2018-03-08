from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class APITestCase(object):

    @chainable
    def assertApi(self, object, method, input, claims):
        registered_callable = getattr(object, method)
        result = yield registered_callable.wrapped(object, input, claims)
        return_value(result)
