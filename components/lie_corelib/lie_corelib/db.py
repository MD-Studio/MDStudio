from typing import *
from autobahn.wamp.protocol import ApplicationSession
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from enum import Enum


class SortMode(Enum):
    Asc = "asc"
    Desc = "desc"

class Collection(dict):
    # type: str
    name = None
    # type: str
    namespace = None

    def __init__(self, name, namespace):
        # type: (str, str) -> None
        self.name = name
        self.namespace = namespace

        dict.__init__(self, name=name, namespace=namespace)

class UpdateManyResponse:
    # type: int
    matched_count = 0
    # type: int
    modified_count = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched_count = response['matched']
        self.modified_count = response['modifiedCount']
        self.upserted_id = response.get('upsertedId')

class UpdateOneResponse:
    # type: int
    matched_count = 0
    # type: int
    modified_count = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched_count = response['matched']
        self.modified_count = response['modifiedCount']
        self.upserted_id = response.get('upsertedId')

class IDatabaseWrapper:
    def count(self, collection=None, filter=None, skip=0, limit=0):
        raise NotImplementedError('Subclass should implement this')

    def delete_one(self, collection=None, filter=None):
        raise NotImplementedError('Subclass should implement this')

    def delete_many(self, collection=None, filter=None):
        raise NotImplementedError('Subclass should implement this')

    def find_one(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        raise NotImplementedError('Subclass should implement this')

    def find_many(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        raise NotImplementedError('Subclass should implement this')

    def insert_one(self, collection=None, insert=None, date_fields=None):
        raise NotImplementedError('Subclass should implement this')

    def insert_many(self, collection=None, insert=None, date_fields=None):
        raise NotImplementedError('Subclass should implement this')

    def update_one(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        raise NotImplementedError('Subclass should implement this')

    def update_many(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        raise NotImplementedError('Subclass should implement this')
        
    def extract(self, result, property):
        raise NotImplementedError('Subclass should implement this')
        
    def transform(self, result, transformed):
        raise NotImplementedError('Subclass should implement this')

class SessionDatabaseWrapper(IDatabaseWrapper):
    def __init__(self, session):
        self.session = session
        self.namespace = session.component_info.get('namespace')

    def count(self, collection=None, filter=None, skip=0, limit=0):
        # type: (Union[str, Dict[str, str], Collection], dict, int, int) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        if skip > 0:
            request['skip'] = skip
        if limit > 0:
            request['limit'] = limit

        return self.session.call(u'liestudio.db.count.{}'.format(self.namespace), request)

    def delete_one(self, collection=None, filter=None):
        # type: (Union[str, Dict[str, str], Collection], dict) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        return self.session.call(u'liestudio.db.deleteone.{}'.format(self.namespace), request)

    def delete_many(self, collection=None, filter=None):
        # type: (Union[str, Dict[str, str], Collection], dict) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        return self.session.call(u'liestudio.db.deletemany.{}'.format(self.namespace), request)

    def find_one(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        # type: (Union[str, Dict[str, str], Collection], dict, Dict[str, bool], int, Optional[List[Tuple[str, SortMode]]]) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'liestudio.db.findone.{}'.format(self.namespace), request)

    def find_many(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        # type: (Union[str, Dict[str, str], Collection], dict, Dict[str, bool], int, Optional[List[Tuple[str, SortMode]]]) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'liestudio.db.findmany.{}'.format(self.namespace), request)

    def insert_one(self, collection=None, insert=None, date_fields=None):
        # type: (Union[str, Dict[str, str], Collection], dict, List[Union[str,List[str]]]) -> Deferred
        request = {'collection': collection}
        if insert:
            request['insert'] = insert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'liestudio.db.insertone.{}'.format(self.namespace), request)

    def insert_many(self, collection=None, insert=None, date_fields=None):
        # type: (Union[str, Dict[str, str], Collection], dict, List[Union[str,List[str]]]) -> Deferred
        request = {'collection': collection}
        if insert:
            request['insert'] = insert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'liestudio.db.insertmany.{}'.format(self.namespace), request)

    def update_one(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        # type: (Union[str, Dict[str, str], Collection], dict, dict, bool, List[Union[str,List[str]]]) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'liestudio.db.updateone.{}'.format(self.namespace), request)

    def update_many(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        # type: (Union[str, Dict[str, str], Collection], dict, dict, bool, List[Union[str,List[str]]]) -> Deferred
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'liestudio.db.updatemany.{}'.format(self.namespace), request)

    @inlineCallbacks
    def extract(self, result, property):
        res = yield result
        returnValue(res[property])

    @inlineCallbacks
    def transform(self, result, transformed):
        res = yield result
        returnValue(None if res is None else transformed(res))


class Model:
    def __init__(self, database_wrapper, collection):
        # type: (Union[SessionDatabaseWrapper, Any], Union[str, Dict[str, str], Collection]) -> None
        if isinstance(database_wrapper, ApplicationSession):
            self.database_wrapper = SessionDatabaseWrapper(database_wrapper)
        else:
            self.database_wrapper = database_wrapper

        self.collection = collection

    def count(self, filter=None, skip=0, limit=0):
        # type: (dict, int, int) -> Union[int, Deferred]
        return self.database_wrapper.extract(self.database_wrapper.count(self.collection, filter, skip, limit), 'total')

    def delete_one(self, filter=None):
        # type: (dict) -> Union[int, Deferred]
        return self.database_wrapper.extract(self.database_wrapper.delete_one(self.collection, filter), 'count')

    def delete_many(self, filter=None):
        # type: (dict) -> Union[int, Deferred]
        return self.database_wrapper.extract(self.database_wrapper.delete_many(self.collection, filter), 'count')

    def find_one(self, filter=None, projection=None, skip=0, sort=None):
        # type: (dict, Dict[str, bool], int, Optional[List[Tuple[str, SortMode]]]) -> Union[Optional[dict], Deferred]
        result = self.database_wrapper.find_one(self.collection, filter, projection, skip, sort)
        return self.database_wrapper.extract(result, 'result')

    def find_many(self, filter=None, projection=None, skip=0, sort=None):
        # type: (dict, Dict[str, bool], int, Optional[List[Tuple[str, SortMode]]]) -> Union[List[dict], Deferred]
        results = self.database_wrapper.find_many(self.collection, filter, projection, skip, sort)
        results = self.database_wrapper.extract(results, 'results')

        return self.database_wrapper.transform(results)

    def insert_one(self, insert=None, date_fields=None):
        # type: (dict, List[Union[str,List[str]]]) -> Union[str, Deferred]
        return self.database_wrapper.extract(self.database_wrapper.insert_one(self.collection, insert, date_fields), 'id')

    def insert_many(self, insert=None, date_fields=None):
        # type: (dict, List[Union[str,List[str]]]) -> Union[List[str], Deferred]
        return self.database_wrapper.extract(self.database_wrapper.insert_many(self.collection, insert, date_fields), 'ids')

    def update_one(self, filter=None, update=None, upsert=False, date_fields=None):
        # type: (dict, dict, bool, List[Union[str,List[str]]]) -> Union[UpdateOneResponse, Deferred]
        return self.database_wrapper.transform(self.database_wrapper.update_one(self.collection, filter, update, upsert, date_fields), UpdateOneResponse)

    def update_many(self, filter=None, update=None, upsert=False, date_fields=None):
        # type: (dict, dict, bool, List[Union[str,List[str]]]) -> Union[UpdateManyResponse, Deferred]
        return self.database_wrapper.transform(self.database_wrapper.update_many(self.collection, filter, update, upsert, date_fields), UpdateManyResponse)
