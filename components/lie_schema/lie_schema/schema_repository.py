import json
from collections import OrderedDict
from pprint import pprint

import dictdiffer
import hashlib
from datetime import datetime

import itertools

from lie_schema.exception import SchemaException
from mdstudio.db.connection import ConnectionType
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable


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

                # if the changes found are not compatible with the latest stored version
                # this call will throw an exception
                yield from self._check_stored_compatibility(component, name, schema, vendor, version)

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
                            'createdAt': datetime.utcnow(),
                            'createdBy': {
                                'username': claims.get('username'),
                                'groups': claims.get('groups')
                            }
                        }
                    }
                }, upsert=True, return_updated=True)

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
                    'updatedAt': datetime.utcnow()
                }, upsert=True)

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

    @staticmethod
    def check_compatible(original, new):
        changeable_keywords = ['title', 'description', 'examples']
        difference = list(itertools.islice(dictdiffer.diff(original, new, ignore=changeable_keywords, expand=True), 5))
        return len(difference) == 0, difference

    @chainable
    def _check_stored_compatibility(self, component, name, schema, vendor, version):
        old = yield self.find_latest(vendor, component, name, version)
        if old:
            old_schema = json.loads(old['schema'])
            compatible, changes = SchemaRepository.check_compatible(old_schema, schema['schema'])
        else:
            compatible = True
            changes = None
        if not compatible:
            err_str = "The new schema is not compatible with the old version that was already registered."
            if changes:
                err_str += " Incompatible changes were:\n"
                for c in changes:
                    if c[0] == 'change':
                        err_str += '\t- Changed value "{}" from "{}" to "{}"\n'.format(c[1], c[2][0], c[2][1])
                    if c[0] == 'add':
                        err_str += '\t- Added "{}.{}" with value "{}"\n'.format(c[1], c[2][0][0], c[2][0][1])
                    if c[0] == 'remove':
                        err_str += '\t- Removed "{}.{}" with value "{}"\n'.format(c[1], c[2][0][0], c[2][0][1])

            raise SchemaException(err_str)

