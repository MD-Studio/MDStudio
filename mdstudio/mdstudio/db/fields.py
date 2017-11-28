import datetime
from typing import List, Callable, Optional, Union

import base64
import hashlib
import pytz
from copy import deepcopy
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from mdstudio.compat import unicode
from mdstudio.db.exception import DatabaseException
from mdstudio.utc import from_utc_string, from_date_string


class Fields(object):
    # type: List[str]
    date_times = []

    # type: List[str]
    dates = []

    # type: List[str]
    encrypted = []

    # type: List[str]
    hashed = []

    _key_repository = None
    _encrypted_prefix = '__encrypted__'

    def __init__(self, date_times=None, dates=None, encrypted=None, hashed=None, key_repository=None):
        # type: (Optional[Union[List[str],str]], Optional[Union[List[str],str]], Optional[Union[List[str],str]], Optional[Union[List[str],str]], Optional[KeyRepository]) -> None
        if date_times and not isinstance(date_times, list):
            date_times = [date_times]
        if dates and not isinstance(dates, list):
            dates = [dates]
        if encrypted and not isinstance(encrypted, list):
            encrypted = [encrypted]
        if hashed and not isinstance(hashed, list):
            hashed = [hashed]

        self.date_times = date_times if date_times else self.date_times
        self.dates = dates if dates else self.dates
        self.encrypted = encrypted if encrypted else self.encrypted
        self.hashed = hashed if hashed else self.hashed

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
        self.transform_to_object(obj, self.hashed, Fields.parse_hashed, prefixes)

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
            for p in prefixes:
                if p and not f.startswith('{}.'.format(p)):
                    nfields.append('{}.{}'.format(p, f))
                else:
                    nfields.append(f)

        for field in nfields:
            split_fields = field.split('.')
            self.transform_docfield_to_object(document, split_fields, parser, **kwargs)

    def transform_docfield_to_object(self, doc, field, parser, **kwargs):
        # type: (dict, Optional[List[str]], Callable) -> None

        subdoc = doc
        for i, level in enumerate(field[:-1]):
            if isinstance(subdoc, dict):
                if level in subdoc:
                    subdoc = subdoc[level]
                else:
                    for key, val in subdoc.items():
                        if key.startswith('$'):
                            self.transform_docfield_to_object(val, field[i:], parser, **kwargs)
                        elif '.' in key:
                            accessor = None
                            keys = key.split('.')
                            nfields = deepcopy(field[i:])
                            for vkey in deepcopy(keys):

                                if not nfields:
                                    break

                                if not accessor:
                                    accessor = vkey
                                else:
                                    accessor = '{}.{}'.format(accessor, vkey)
                                # remove front from list
                                if nfields[0] == vkey:
                                    nfields.pop(0)
                                if accessor in subdoc:
                                    self.transform_docfield_to_object(subdoc, [accessor] + nfields, parser, **kwargs)

                    subdoc = None
            else:
                if isinstance(subdoc, list):
                    for d in subdoc:
                        self.transform_docfield_to_object(d, field[i:], parser, **kwargs)
                subdoc = None
                break

        if isinstance(subdoc, dict):
            for key, val in subdoc.items():
                if key.startswith('$'):
                    self.transform_docfield_to_object(val, [field[-1]], parser, **kwargs)

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
                if isinstance(subdoc[key], dict):
                    for dkey, val in subdoc[key].items():
                        if dkey.startswith('$') and dkey in self.conversion_operators:
                            subdoc[key][dkey] = parser(self, val, subdoc, key, **kwargs)
                elif isinstance(subdoc[key], list):
                    for i, e in enumerate(subdoc[key]):
                        subdoc[key][i] = parser(self, e, subdoc, key, **kwargs)
                else:
                    subdoc[key] = parser(self, subdoc[key], subdoc, key, **kwargs)

    def parse_date_time(self, val, sub, key, *args, **kwargs):
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
            raise DatabaseException("Failed to parse datetime field '{}' with key '{}'".format(val, key))

    def parse_date(self, val, sub, key, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            return from_date_string(val)
        elif isinstance(val, datetime.datetime):
            return val.date()
        elif isinstance(val, datetime.date):
            return val
        else:
            raise DatabaseException("Failed to parse date field '{}' with key {}".format(val, key))

    def parse_encrypted(self, val, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            val = val.encode()
        try:
            if isinstance(val, bytes):
                val = '{}:{}'.format(self._encrypted_prefix, kwargs['encryptor'].encrypt(val).decode('utf-8'))
            else:
                raise DatabaseException("Failed to encrypt field '{}'".format(val))
        except Exception as ex:
            raise ex
        else:
            return val

    def parse_hashed(self, val, sub, key, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            sval = val.encode()
        else:
            sval = deepcopy(val)
        try:
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=hashlib.sha512(sval).digest(),
                iterations=50000,
                backend=default_backend()
            )
            sub['__hashed__:{}'.format(key)] = base64.urlsafe_b64encode(kdf.derive(sval)).decode('utf-8')
        except Exception as ex:
            raise ex
        else:
            return val

    def decrypt(self, val, sub, key, *args, **kwargs):
        if isinstance(val, (str, unicode)):
            val = val.encode()
        if isinstance(val, bytes):
            prefix = '{}:'.format(self._encrypted_prefix)
            try:
                if prefix in val.decode('utf-8'):
                    val = kwargs['encryptor'].decrypt(val.replace(prefix.encode(), b'', 1))
                else:
                    raise DatabaseException(
                        'Trying to decrypt an unencrypted field with key "{key}", please check your insert statements!'.format(
                            key=key))
            except Exception as ex:
                raise DatabaseException('Failed to decrypt field {key}:\n{exp_str}'.format(key=key, exp_str=str(ex)))
            else:
                return val.decode('utf-8')
        else:
            raise DatabaseException("Failed to decrypt field '{}'".format(val))

    def get_encryptor(self, claims):
        from cryptography.fernet import Fernet
        try:
            encryptor = Fernet(self._get_key(claims))
        except Exception:
            raise DatabaseException('Failed to create a Fernet encryption class due to an incorrect key.')
        else:
            return encryptor

    @property
    def conversion_operators(self):
        return ['$eq', '$gt', '$gte', '$in', '$lt', '$lte', '$ne', '$nin',
                '$and', '$not', '$nor', '$or',
                '$all', '$elemMatch',
                '$set', '$setOnInsert',
                '$addToSet', '$pull', '$push',
                '$each']

    def _get_key(self, claims):
        return self._key_repository.get_key(claims)
