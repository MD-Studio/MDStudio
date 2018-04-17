import twisted.trial.unittest as trial_unit
from unittest2.case import _AssertRaisesContext

create_mock_client = False


class DBTestCase(trial_unit.TestCase):
    def run(self, result=None):
        global create_mock_client
        create_mock_client = True

        result = super(DBTestCase, self).run(result=result)

        create_mock_client = False

        return result

    def assertRaisesRegex(self, expected_exception, expected_regex,
                          *args, **kwargs):
        """Asserts that the message in a raised exception matches a regex.

        Args:
            expected_exception: Exception class expected to be raised.
            expected_regex: Regex (re pattern object or string) expected
                    to be found in error message.
            args: Function to be called and extra positional args.
            kwargs: Extra kwargs.
        """
        context = _AssertRaisesContext(expected_exception, self, expected_regex)
        return context.handle('assertRaisesRegex', args, kwargs)