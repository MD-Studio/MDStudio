# -*- coding: utf-8 -*-

"""
file: model_date_time.py

Graph model classes for dealing with date/time definitions
"""

import pytz
import logging

from datetime import datetime, date, time
from dateutil.parser import parse

from lie_graph.graph_mixin import NodeEdgeToolsBaseClass


def to_datetime(value, instance):
    """
    Parse a string representation of a datetime, date or time to their
    respective Python datetime.datetime, datetime.date and datetime.time object

    :param value:    string to parse
    :param instance: datetime, date or time objects the string should represent

    :return:         Python datetime.datetime, datetime.date or datetime.time object
    """

    # If value is a datetime object, parse to string
    if isinstance(value, instance):
        return value

    # If it is a string, try parse to datetime object
    elif isinstance(value, str):

        try:
            parsed = parse(value)
        except ValueError:
            logging.error('{0} is not a valid date-time representation')
            return

        # fix for python < 3.6
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=pytz.utc)

        return parsed


class DateTime(NodeEdgeToolsBaseClass):

    def now(self):
        """
        Return a Python datetime.datetime object representing the current
        date-time respecting local timezone.

        :rtype: :py:datetime:datetime
        """

        dt = datetime.now(tz=pytz.utc)
        return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)

    def datetime(self):
        """
        Return a Python datetime object representing the stored date-time

        :rtype: :py:datetime:datetime
        """

        return to_datetime(self.get(), datetime)

    def set(self, key, value=None):
        """
        Set and validate an ISO string representation of a date-time instance
        in accordance to RFC 3339
        """

        if key == self.node_value_tag:
            dt = to_datetime(value, datetime)
            if dt:
                value = dt.astimezone(pytz.utc).isoformat()
            else:
                logging.error('Unsupported format for date-time {0}'.format(type(value)))
                return

        self.nodes[self.nid][key] = value


class Date(NodeEdgeToolsBaseClass):

    def now(self):
        """
        Return a Python datetime.datetime object representing the current date.

        :rtype: :py:datetime:date
        """

        return datetime.now(tz=pytz.utc).date()

    def datetime(self):
        """
        Return a Python datetime object representing the stored date

        :rtype: :py:datetime:date
        """

        return to_datetime(self.get(), date)

    def set(self, key, value=None):
        """
        Set and validate an ISO string representation of a date instance
        in accordance to RFC 3339
        """

        if key == self.node_value_tag:
            dt = to_datetime(value, date)
            if dt:
                value = dt.isoformat()
            else:
                logging.error('Unsupported format for date-time {0}'.format(type(value)))
                return

        self.nodes[self.nid][key] = value


class Time(NodeEdgeToolsBaseClass):

    def now(self):
        """
        Return a Python datetime.datetime object representing the current
        time respecting local timezone.

        :rtype: :py:datetime:time
        """

        return datetime.now(tz=pytz.utc).time()

    def datetime(self):
        """
        Return a Python datetime object representing the stored time

        :rtype: :py:datetime:time
        """

        return to_datetime(self.get(), time)

    def set(self, key, value=None):
        """
        Set and validate an ISO string representation of a time instance
        in accordance to RFC 3339
        """

        if key == self.node_value_tag:
            dt = to_datetime(value, time)
            if dt:
                value = dt.isoformat()
            else:
                logging.error('Unsupported format for date-time {0}'.format(type(value)))
                return

        self.nodes[self.nid][key] = value