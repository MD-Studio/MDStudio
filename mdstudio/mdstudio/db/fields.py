import datetime
from typing import List, Callable, Optional

import pytz

from mdstudio.db.exception import DatabaseException
from mdstudio.logging.logger import Logger
from mdstudio.utc import from_utc_string, from_date_string
from mdstudio.compat import unicode


class Fields(object):
    # type: List[str]
    date_times = []

    # type: List[str]
    dates = []

    # type: List[str]
    encrypted = []

    _key_repository = None
    _encrypted_prefix = '__encrypted__'

    _logger = Logger()

    def __init__(self, date_times=None, dates=None, encrypted=None, key_repository=None):
        # type: (Optional[List[str]], Optional[List[str]], Optional[List[str]], Optional[KeyRepository]) -> None
        if date_times and not isinstance(date_times, list):
            date_times = [date_times]
        if dates and not isinstance(dates, list):
            dates = [dates]
        if encrypted and not isinstance(encrypted, list):
            encrypted = [encrypted]

        self.date_times = date_times if date_times else self.date_times
        self.dates = dates if dates else self.dates
        self.encrypted = encrypted if encrypted else self.encrypted

        self._key_repository = key_repository

    def __eq__(self, other):
        # type: (Fields) -> bool
        return other and set(self.date_times) == set(other.date_times) \
               and set(self.dates) == set(other.dates) \
               and set(self.encrypted) == set(other.encrypted)

    def merge(self, other):
        # type: (Fields) -> Fields
        return Fields(date_times=other.date_times + self.date_times,
                      dates=other.dates + self.dates,
                      encrypted=other.encrypted + self.encrypted)

    def convert_call(self, obj, prefixes=None, claims=None):
        # type: (dict, Optional[List[str]], Optional[dict]) -> None
        self.transform_to_object(obj, self.date_times, Fields.parse_date_time, prefixes)
        self.transform_to_object(obj, self.dates, Fields.parse_date, prefixes)

        if claims and self.uses_encryption:
            encryptor = self.get_encryptor(claims)
            self.transform_to_object(obj, self.encrypted, Fields.parse_encrypted, prefixes, **{'encryptor': encryptor})

    def parse_result(self, obj, claims=None):
        # type: (dict, dict) -> None
        if claims and self.uses_encryption:
            encryptor = self.get_encryptor(claims)
            self.transform_to_object(obj, self.encrypted, Fields.decrypt, None, **{'encryptor': encryptor})

    def is_empty(self):
        # type: () -> bool
        return not self.date_times and not self.dates and not self.encrypted

    def to_dict(self):
        # type: () -> dict
        result = {}
        if self.date_times:
            result['datetime'] = self.date_times
        if self.dates:
            result['date'] = self.dates
        if self.encrypted:
            result['encrypted'] = self.encrypted
        return result

    @property
    def uses_encryption(self):
        # type: () -> bool
        return len(self.encrypted) > 0

    @staticmethod
    def from_dict(request, key_repository=None):
        # type: (dict, KeyRepository) -> Fields
        return Fields(date_times=request.get('datetime'),
                      dates=request.get('date'),
                      encrypted=request.get('encrypted'),
                      key_repository=key_repository)

    def transform_to_object(self, document, fields, parser, prefixes, **kwargs):
        # type: (dict, List[str], Callable, Optional[List[str]]) -> None
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
            self.transform_docfield_to_object(document, split_fields, parser, **kwargs)

    def transform_docfield_to_object(self, doc, field, parser, **kwargs):
        # type: (dict, Optional[List[str]], Callable) -> None
        subdoc = doc

        for level in field[:-1]:
            if isinstance(subdoc, dict) and level in subdoc:
                subdoc = subdoc[level]
            else:
                if isinstance(subdoc, list):
                    for d in subdoc:
                        self.transform_docfield_to_object(d, field[1:], parser, **kwargs)
                subdoc = None
                break
        if isinstance(subdoc, dict):
            for key, val in subdoc.items():
                if key.startswith('$'):
                    self.transform_docfield_to_object(val, field[1:], parser, **kwargs)

        if subdoc is None:
            return

        key = field[-1]

        # if we have a list of objects we support just indexing those
        if isinstance(subdoc, list):
            for d in subdoc:
                if key in d:
                    d[key] = parser(self, d[key], d, key, **kwargs)
        else:
            # either we indexed a normal datetime field, or a list with datetimes
            if key in subdoc:
                if isinstance(subdoc[key], list):
                    for i, e in enumerate(subdoc[key]):
                        subdoc[key][i] = parser(self, e, subdoc, key, **kwargs)
                else:
                    subdoc[key] = parser(self, subdoc[key], subdoc, key, **kwargs)

    def parse_date_time(self, val, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            return from_utc_string(val)
        elif isinstance(val, datetime.datetime):
            if not val.tzinfo:
                raise DatabaseException(
                    "No timezone information found. All datetime info should be stored in UTC format, "
                    "please use 'mdstudio.utc.now()' and 'mdstudio.utc.to_utc_string()'")
            if val.tzinfo != pytz.utc:
                val = val.astimezone(pytz.utc)
            return val
        else:
            raise DatabaseException("Failed to parse datetime field '{}'".format(val))

    def parse_date(self, val, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            return from_date_string(val)
        elif isinstance(val, datetime.datetime):
            return val.date()
        elif isinstance(val, datetime.date):
            return val
        else:
            raise DatabaseException("Failed to parse date field '{}'".format(val))

    def parse_encrypted(self, val, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            val = val.encode()
        if isinstance(val, bytes):
            return '{}:{}'.format(self._encrypted_prefix, kwargs['encryptor'].encrypt(val).decode('utf-8'))
        else:
            raise DatabaseException("Failed to encrypt field '{}'".format(val))

    def decrypt(self, val, key, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            val = val.encode()
        if isinstance(val, bytes):
            prefix = '{}:'.format(self._encrypted_prefix)
            if prefix in val.decode('utf-8'):
                return kwargs['encryptor'].decrypt(val.replace(prefix.encode(), b'', 1)).decode('utf-8')
            else:
                self._logger.warn('Trying to decrypt an unencrypted field with key "{}}", please check your insert statements!'.format(key))
                return val
        else:
            raise DatabaseException("Failed to decrypt field '{}'".format(val))

    def get_encryptor(self, claims):
        from cryptography.fernet import Fernet
        encryptor = Fernet(self._get_key(claims))
        return encryptor

    def _get_key(self, claims):
        return self._key_repository.get_key(claims)
