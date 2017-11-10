from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


class TestSession:
    procedure = "test.procedure"

class APITestCase:

    @chainable
    def assertApi(self, object, method, input, auth_meta):
        registered_callable = getattr(object, method)
        print("yield")
        result = yield registered_callable.wrapped(object, input, TestSession(), auth_meta)
        print("result")
        return_value(result)
