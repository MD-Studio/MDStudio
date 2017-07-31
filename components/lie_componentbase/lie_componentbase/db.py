from autobahn.wamp.protocol import ApplicationSession

class SessionDatabaseWrapper:
    def __init__(self, session):
        self.session = session
        self.namespace = session.component_info.get('namespace')

    def count(self, collection=None, filter=None, skip=0, limit=0):
        request = {'collection': collection, 'filter': filter or {}}

        if skip > 0:
            request['skip'] = skip
        if limit > 0:
            request['limit'] = limit

        return self.session.call(u'liestudio.db.count.{}'.format(self.namespace), request)

    def delete_one(self, collection=None, filter=None):
        request = {'collection': collection, 'filter': filter or {}}


        return self.session.call(u'liestudio.db.deleteone.{}'.format(self.namespace), request)

    def delete_many(self, collection=None, filter=None):
        request = {'collection': collection, 'filter': filter or {}}


        return self.session.call(u'liestudio.db.deletemany.{}'.format(self.namespace), request)

    def find_one(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'liestudio.db.findone.{}'.format(self.namespace), request)

    def find_many(self, collection=None, filter=None, projection=None, skip=0, sort=None):
        request = {'collection': collection, 'filter': filter or {}}

        if projection:
            request['projection'] = projection
        if skip > 0:
            request['skip'] = skip
        if sort:
            request['sort'] = sort

        return self.session.call(u'liestudio.db.findmany.{}'.format(self.namespace), request)

    def insert_one(self, collection=None, insert=None, date_fields=None):
        request = {'collection': collection}
        if insert:
            request['insert'] = insert
        if date_fields:
            request['dateFields'] = date_fields

        return self.session.call(u'liestudio.db.insertone.{}'.format(self.namespace), request)

    def insert_many(self, collection=None, insert=None, date_fields=None):
        request = {'collection': collection}
        if insert:
            request['insert'] = insert
        if date_fields:
            request['dateFields'] = date_fields

        return self.session.call(u'liestudio.db.insertmany.{}'.format(self.namespace), request)

    def update_one(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['dateFields'] = date_fields

        return self.session.call(u'liestudio.db.updateone.{}'.format(self.namespace), request)

    def update_many(self, collection=None, filter=None, update=None, upsert=False, date_fields=None):
        request = {'collection': collection, 'filter': filter or {}}

        if update:
            request['update'] = update
        if upsert:
            request['upsert'] = upsert
        if date_fields:
            request['dateFields'] = date_fields

        return self.session.call(u'liestudio.db.updatemany.{}'.format(self.namespace), request)

class Model:
    def __init__(self, database_wrapper, collection):
        if isinstance(database_wrapper, ApplicationSession):
            self.database_wrapper = SessionDatabaseWrapper(database_wrapper)
        else:
            self.database_wrapper = database_wrapper
    
        self.collection = collection

    def count(self, filter=None, skip=0, limit=0):
        return self.database_wrapper.count(self.collection, filter, skip, limit)

    def delete_one(self, filter=None):
        return self.database_wrapper.delete_one(self.collection, filter)

    def delete_many(self, filter=None):
        return self.database_wrapper.delete_many(self.collection, filter)

    def find_one(self, filter=None, projection=None, skip=0, sort=None):
        return self.database_wrapper.find_one(self.collection, filter, projection, skip, sort)

    def find_many(self, filter=None, projection=None, skip=0, sort=None):
        return self.database_wrapper.find_many(self.collection, filter, projection, skip, sort)

    def insert_one(self, insert=None, date_fields=None):
        return self.database_wrapper.insert_one(self.collection, insert, date_fields)

    def insert_many(self, insert=None, date_fields=None):
        return self.database_wrapper.insert_many(self.collection, insert, date_fields)

    def update_one(self, filter=None, update=None, upsert=False, date_fields=None):
        return self.database_wrapper.update_one(self.collection, filter, update, upsert, date_fields)

    def update_many(self, filter=None, update=None, upsert=False, date_fields=None):
        return self.database_wrapper.update_many(self.collection, filter, update, upsert, date_fields)