import datetime

import pytz
from typing import List

from mdstudio.db.exception import DatabaseException

from mdstudio.utc import from_utc_string, from_date_string


class Fields(object):
    date_times = []
    dates = []
    protected = []

    def __init__(self, *args, date_times=None, dates=None, protected=None):
        # type: (List[str], List[str], List[str]) -> None
        self.date_times = date_times if date_times else self.date_times
        self.dates = dates if dates else self.dates
        self.protected = protected if protected else self.protected

    def __eq__(self, other):
        return other and set(self.date_times) == set(other.date_times) \
               and set(self.dates) == set(other.dates) \
               and set(self.protected) == set(other.protected)

    def merge(self, other):
        # type: (Fields) -> Fields
        return Fields(date_times=other.date_times + self.date_times,
                      dates=other.dates + self.dates,
                      protected=other.protected + self.protected)

    def convert_call(self, obj, prefixes=None):
        self.transform_to_object(obj, self.date_times, Fields.parse_date_time, prefixes)
        self.transform_to_object(obj, self.dates, Fields.parse_date, prefixes)

    def is_empty(self):
        return not self.date_times and not self.dates and not self.protected

    def to_dict(self):
        result = {}
        if self.date_times:
            result['datetime'] = self.date_times
        if self.dates:
            result['date'] = self.dates
        if self.protected:
            result['protected'] = self.protected
        return result

    def from_dict(self, request):
        if 'datetime' in request:
            self.date_times = request['datetime']
        if 'date' in request:
            self.dates = request['date']
        if 'protected' in request:
            self.protected = request['protected']

        return self

    @staticmethod
    def transform_to_object(document, fields, parser, prefixes=None):
        if prefixes is None:
            prefixes = ['']

        nfields = []
        for f in fields:
            if all(not f.startswith(p) for p in prefixes):
                for p in prefixes:
                    nfields.append('{}.{}'.format(p, f))
            else:
                nfields.append(f)

        for field in nfields:
            split_fields = field.split('.')
            Fields.transform_docfield_to_object(document, split_fields, parser)

    @staticmethod
    def transform_docfield_to_object(doc, field, parser):
        subdoc = doc

        for level in field[:-1]:
            if isinstance(subdoc, dict) and level in subdoc:
                subdoc = subdoc[level]
            else:
                if isinstance(subdoc, list):
                    for d in subdoc:
                        Fields.transform_docfield_to_object(d, field[1:], parser)
                subdoc = None
                break

        if subdoc is None:
            return

        key = field[-1]

        # if we have a list of objects we support just indexing those
        if isinstance(subdoc, list):
            for d in subdoc:
                if key in d:
                    d[key] = parser(d[key])
        else:
            # either we indexed a normal datetime field, or a list with datetimes
            if key in subdoc:
                if isinstance(subdoc[key], list):
                    for i, e in enumerate(subdoc[key]):
                        subdoc[key][i] = parser(e)
                else:
                    subdoc[key] = parser(subdoc[key])

    @staticmethod
    def parse_date_time(val):
        if isinstance(val, str):
            return from_utc_string(val)
        elif isinstance(val, datetime.datetime):
            if not val.tzinfo:
                raise DatabaseException("No timezone information found. All datetime info should be stored in UTC format, please use 'mdstudio.utc.now()' and 'mdstudio.utc.to_utc_string()'")
            if val.tzinfo != pytz.utc:
                val = val.astimezone(pytz.utc)
            return val
        else:
            raise DatabaseException("Failed to parse datetime field '{}'".format(val))

    @staticmethod
    def parse_date(val):
        if isinstance(val, str):
            return from_date_string(val)
        elif isinstance(val, datetime.datetime):
            return val.date()
        elif isinstance(val, datetime.date):
            return val
        else:
            raise DatabaseException("Failed to parse date field '{}'".format(val))
