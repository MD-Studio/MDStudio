from twisted.trial.unittest import TestCase

from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.util import validate_input, validate_output


class TestSession:
    procedure = "test.procedure"

class APITestCase(TestCase):

    @chainable
    def assertApi(self, object, method, input, output):
        registered_callable = getattr(object, method)
        result = yield registered_callable.wrapped(object, input, TestSession())
        self.assertEqual(result, output)
