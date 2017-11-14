from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class TestSession:
    procedure = "test.procedure"

class APITestCase:

    @chainable
    def assertApi(self, object, method, input, claims, details=True):
        registered_callable = getattr(object, method)
        if details:
            result = yield registered_callable.wrapped(object, input, claims, **{'details': TestSession()})
        else:
            result = yield registered_callable.wrapped(object, input, claims)
        return_value(result)
