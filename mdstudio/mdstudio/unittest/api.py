from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.util import validate_input, validate_output


class TestSession:
    procedure = "test.procedure"

class APITestCase:

    @chainable
    def assertApi(self, object, method, input):
        registered_callable = getattr(object, method)
        result = yield registered_callable.wrapped(object, input, TestSession())
        return result
