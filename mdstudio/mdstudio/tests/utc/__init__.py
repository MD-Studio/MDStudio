from unittest import TestCase

from datetime import datetime, timedelta

import pytz
from faker import Faker

from mdstudio.utc import now, today, from_utc_string, to_utc_string, to_date_string, from_date_string


class TestUTC(TestCase):

    faker = Faker()

    def test_now(self):
        self.assertLess(now() - datetime.now(tz=pytz.utc), timedelta(seconds=1))

    def test_today(self):
        self.assertEqual(today(), now().date())

    def test_utc(self):

        for i in range(100):
            n = self.faker.iso8601(tzinfo=pytz.utc)
            self.assertEqual(to_utc_string(from_utc_string(n)), n)

    def test_utc2(self):

        for i in range(100):
            tz = pytz.timezone('Pacific/Johnston')
            n = self.faker.date_time(tzinfo=tz)
            self.assertEqual(from_utc_string(n.isoformat()), n)

    def test_date(self):

        for i in range(100):
            n = self.faker.date()
            self.assertEqual(to_date_string(from_date_string(n)), n)