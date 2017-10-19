import unittest
import twisted.trial.unittest as trial_unit

create_mock_client = False

class DBTestCase(unittest.TestCase):
    def run(self, result=None):
        global create_mock_client
        create_mock_client = True

        result = super().run(result=result)

        create_mock_client = False

        return result


class TrialDBTestCase(trial_unit.TestCase):
    def run(self, result=None):
        global create_mock_client
        create_mock_client = True

        result = super().run(result=result)

        create_mock_client = False

        return result
