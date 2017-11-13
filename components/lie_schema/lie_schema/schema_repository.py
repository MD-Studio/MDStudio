import datetime
import json
from pprint import pprint

import hashlib
from autobahn.util import utcnow

from mdstudio.db.connection import ConnectionType
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock


class SchemaRepository:

    class Schemas(Model):
        """
        Schema:
        {
            'vendor': <vendor>,
            'component': <component>,
            'name: <name>
            'hash': <hash>,
            'major': <version>,
            'build': <build>,
            'schema': <schema>,
            'updatedAt': <datetime>
        }
        """
        connection_type = ConnectionType.User

        def __init__(self, wrapper=None, collection=None):
            super().__init__(wrapper=wrapper, collection=collection)

    class History(Model):
        """
        Schema:
        {
            'vendor': <vendor>,
            'component': <component>,
            'version': <version>,
            'name': <name>
            'builds': [
                {
                    'schema': <schema>,
                    'hash': <hash>,
                    'createdAt': <time>,
                    'createdBy': {
                        'user': <user>,
                        'group: <group>,
                        'groupRole': <groupRole>
                    }
                }
            ]
        }
        """
        connection_type = ConnectionType.User

        def __init__(self, wrapper=None, collection=None):
            super().__init__(wrapper=wrapper, collection=collection)

    def __init__(self, session, type):
        # type: (SchemaWampApi, str) -> None
        self.session = session
        self.type = type

    def find_latest(self, vendor, component, name, version, schema_str=None):
        key = {
            'vendor': vendor,
            'component': component,
            'version': version,
            'name': name
        }
        if schema_str:
            key['hash'] = self.hash_schema(schema_str)
        return self.schemas.find_one(key)

    @chainable
    def upsert(self, vendor, component, schema, claims):

        schema_str = self.schema_to_string(schema['schema'])
        hash = self.hash_schema(schema_str)
        name = schema['name']
        version = schema['version']
        latest = yield self.find_latest(vendor, component, name, version, schema_str)

        if not latest:
            found = yield self.history.find_one({
                'vendor': vendor,
                'component': component,
                'version': version,
                'name': name,
                'builds': {
                    '$elemMatch': {
                        'hash': hash
                    }
                }
            })

            if not found:
                updated = yield self.history.find_one_and_update({
                    'vendor': vendor,
                    'component': component,
                    'version': version,
                    'name': name,
                }, {
                    '$setOnInsert': {
                        'vendor': vendor,
                        'component': component,
                        'version': version,
                        'name': name
                    },
                    '$addToSet': {
                        'builds': {
                            'hash': hash,
                            'schema': schema_str,
                            'createdAt': utcnow(),
                            'createdBy': {
                                'username': claims.get('username'),
                                'groups': claims.get('groups')
                            }
                        }
                    }
                }, upsert=True, return_updated=True)

                if updated:
                    self.schemas.replace_one({
                        'vendor': vendor,
                        'component': component,
                        'version': version,
                        'name': name,
                    }, {
                        'vendor': vendor,
                        'component': component,
                        'version': version,
                        'name': name,
                        'hash': hash,
                        'major': version,
                        'build': len(updated['builds']),
                        'schema': schema_str,
                        'updatedAt': utcnow()
                    }, upsert=True)
                else:
                    raise NotImplemented()

    @property
    def schemas(self):
        return SchemaRepository.Schemas(self.session, '{}.schema'.format(self.type))

    @property
    def history(self):
        return SchemaRepository.History(self.session, '{}.history'.format(self.type))

    def hash_schema(self, schema):
        return hashlib.sha256(self.schema_to_string(schema).encode()).hexdigest()

    def schema_to_string(self, schema):
        return json.dumps(schema, sort_keys=True)

