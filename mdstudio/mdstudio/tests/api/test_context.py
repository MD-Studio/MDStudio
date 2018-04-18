# coding=utf-8
import random

import mock
from twisted.trial.unittest import TestCase

from mdstudio.api.context import ContextManager
from mdstudio.deferred.chainable import test_chainable as chainable
from mdstudio.deferred.sleep import sleep
from mdstudio.util.random import random_uuid


class ContextTests(TestCase):

    @chainable
    def test_context_twice_nested(self):
        def _get_identifier(expected):
            identifier = ContextManager.get('identifier')
            self.assertEqual(identifier, expected)
            return identifier

        @chainable
        def _test_worker(expected):
            for i in range(100):
                _get_identifier(expected)  # check original context

                yield sleep(random.random() / 100)

                expected_nested1 = '{}-nested1'.format(_get_identifier(expected))  # check context after sleep, prepare for nesting
                with ContextManager({'identifier': expected_nested1}):
                    _get_identifier(expected_nested1)  # check once nested constext

                    yield sleep(random.random() / 100)

                    expected_nested2 = '{}-nested2'.format(
                        _get_identifier(expected_nested1))  # check once nested context after sleep, prepare for second nesting
                    with ContextManager({'identifier': expected_nested2}):
                        _get_identifier(expected_nested2)  # check second nested constext

                        yield sleep(random.random() / 100)

                        _get_identifier(expected_nested2)  # check second nested context after sleep

                        yield sleep(random.random() / 100)  # sleep at end of nesting

                    _get_identifier(expected_nested1)  # check first nesting after second nesting has ended

                    yield sleep(random.random() / 100)

                    _get_identifier(expected_nested1)  # check again after another sleep

                    # don't sleep at the end of this nesting

                _get_identifier(expected)  # check again after both nestings ended

        def _make_test_worker(expected):
            return ContextManager.call_with_context({'identifier': expected}, _test_worker, expected)

        workers = [_make_test_worker(random_uuid()) for _ in range(3)]

        for worker in workers:
            yield worker
