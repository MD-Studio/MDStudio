from twisted.trial.unittest import TestCase

from mdstudio.util import validate_input, validate_output


class TestSession:
    procedure = "test.procedure"

class APITestCase(TestCase):

    def assertApi(self, object, method, input, output):
        registered_callable = getattr(object, method)
        result = validate_input(registered_callable._lie_input_schema)\
            (validate_output(registered_callable._lie_output_schema))(registered_callable)(object, input, TestSession())

        self.assertEqual(result, output)
