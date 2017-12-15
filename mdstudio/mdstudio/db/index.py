from typing import List, Optional

from mdstudio.db.sort_mode import SortMode


class Index(object):

    def __init__(self, keys=None, unique=None, name=None, documentTTL=None):
        # type: (Optional[IndexKeys], Optional[bool], Optional[str], Optional[int]) -> None
        self.keys = keys
        self.unique = unique
        self.name = name
        self.documentTTL = documentTTL

    def to_dict(self, name_exclusive=False, create=True, to_mongo=False):
        # type: (Optional[bool], Optional[bool]) -> dict
        if create:
            kwargs = {
                'background': True
            }
        else:
            kwargs = {}

        if self.name:
            kwargs['name'] = self.name

            if name_exclusive:
                return kwargs

        if self.keys:
            kwargs['keys'] = self.keys
            for i, k in enumerate(kwargs[kwargs['keys']]):
                kwargs['keys'][i][1] = str(kwargs['keys'][i][1])
        if self.unique:
            kwargs['unique'] = self.unique
        if self.documentTTL:
            kwargs['expireAfterSeconds' if to_mongo else 'documentTTL'] = self.documentTTL

        return kwargs

    @staticmethod
    def from_dict(document):
        keys = document.get('keys')
        if keys:
            for i, k in enumerate(keys):
                keys[i][1] = SortMode.from_string(keys[i][1])

        return Index(keys=keys,
                     unique=document.get('unique'),
                     name=document.get('name'),
                     documentTTL=document.get('documentTTL'))