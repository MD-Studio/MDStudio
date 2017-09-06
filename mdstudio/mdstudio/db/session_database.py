from twisted.internet.defer import inlineCallbacks

from mdstudio.mdstudio.db.database import IDatabase
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

class SessionDatabaseWrapper(IDatabase):

    def __init__(self, session):
        self.session = session
        self.namespace = session.component_info.get('namespace')

    def more(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self.session.call(u'mdstudio.db.more.{}'.format(self.namespace), {
            'cursorId': cursor_id
        })

    def rewind(self, cursor_id):
        # type: (str) -> Dict[str, Any]

        return self.session.call(u'mdstudio.db.rewind.{}'.format(self.namespace), {
            'cursorId': cursor_id
        })

    def find_one_and_update(self, collection, query, update, upsert=False, projection=None, sort=None,
                            return_updated=False, date_fields=None):
        pass

    def aggregate(self, pipeline):
        pass

    def find_one_and_delete(self, collection, query, projection=None, sort=None, return_updated=False):
        pass

    def find_one_and_replace(self, collection, query, replacement, upsert=False, projection=None, sort=None,
                             return_updated=False, date_fields=None):
        pass

    def distinct(self, collection, field, query=None):
        pass

    def insert_one(self, collection, insert, date_fields=None):
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.insert_one.{}'.format(self.namespace), request)

    def insert_many(self, collection, insert, date_fields=None):
        request = {
            'collection': collection,
            'insert': insert
        }
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.insert_many.{}'.format(self.namespace), request)

    def replace_one(self, collection, filter, replacement, upsert=False, date_fields=None):
        request = {
            'collection': collection,
            'filter': filter,
            'replacement': replacement,
            'upsert': upsert
        }
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.replace_one.{}'.format(self.namespace), request)






    def count(self, collection=None, filter=None, skip=0, limit=0):
        request = {'collection': collection, 'filter': filter or {}}

        if skip > 0:
            request['skip'] = skip
        if limit > 0:
            request['limit'] = limit

        return self.session.call(u'mdstudio.db.count.{}'.format(self.namespace), request)

    def delete_one(self, collection=None, filter=None):
        request = {'collection': collection, 'filter': filter or {}}

        return self.session.call(u'mdstudio.db.delete_one.{}'.format(self.namespace), request)

    def delete_many(self, collection=None, filter=None):
        request = {'collection': collection, 'filter': filter or {}}

        return self.session.call(u'mdstudio.db.delete_many.{}'.format(self.namespace), request)

    def find_one(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'mdstudio.db.find_one.{}'.format(self.namespace), request)

    def find_many(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'mdstudio.db.find_many.{}'.format(self.namespace), request)

    def update_one(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.update_one.{}'.format(self.namespace), request)

    def update_many(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['fields'] = {'date': date_fields}

        return self.session.call(u'mdstudio.db.update_many.{}'.format(self.namespace), request)

    @inlineCallbacks
    def extract(self, result, property):
        res = yield result
        returnValue(res[property])

    @inlineCallbacks
    def transform(self, result, transformed):
        res = yield result
        returnValue(None if res is None else transformed(res))