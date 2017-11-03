from twisted.trial.unittest import TestCase

from mdstudio.deferred.make_deferred import make_deferred
from mdstudio.util import validate_input, validate_output


class TestSession:
    procedure = "test.procedure"

class APITestCase(TestCase):

    @make_deferred
    def assertApi(self, object, method, input, output):
        registered_callable = getattr(object, method)
        result = yield validate_input(registered_callable._lie_input_schema) \
            (validate_output(registered_callable._lie_output_schema)(registered_callable.wrapped))(input, TestSession())
        self.assertEqual(result, output)
