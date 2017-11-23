import itertools
import json
from pprint import pformat

import dictdiffer
import hashlib
from jsonschema import Draft4Validator, SchemaError

import mdstudio.utc as utc
from lie_schema.exception import SchemaException
from mdstudio.db.connection import ConnectionType
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable


class SchemaRepository(object):

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
        date_time_fields = ['updatedAt']

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
        date_time_fields = ['builds.createdAt']

        def __init__(self, wrapper=None, collection=None):
            super().__init__(wrapper=wrapper, collection=collection)

    def __init__(self, session, type, db_wrapper=None):
        # type: (SchemaWampApi, str) -> None
        self.wrapper = db_wrapper if db_wrapper else session
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
        return self.schemas.find_one(key, projection={
            '_id': False
        })

    @chainable
    def upsert(self, vendor, component, schema, claims):

        try:
            Draft4Validator.check_schema(schema['schema'])
        except SchemaError as e:
            raise SchemaException('Schema does not conform to jsonschema draft 4, '\
                'see http://json-schema.org/ for more info:\n{}\n\n{}'.format(pformat(schema['schema']), e.message))


        schema_str = self.schema_to_string(schema['schema'])
        hash = self.hash_schema(schema_str)
        name = schema['name']
        version = schema['version']
        latest = yield self.find_latest(vendor, component, name, version, schema_str)

        if not latest:
            yield self._upload_new_schema(claims, component, hash, name, schema, schema_str, vendor, version)

    @property
    def schemas(self):
        return SchemaRepository.Schemas(self.wrapper, '{}.schema'.format(self.type))

    @property
    def history(self):
        return SchemaRepository.History(self.wrapper, '{}.history'.format(self.type))

    @property
    def ignored_keywords(self):
        return ['title', 'description', 'examples']

    def hash_schema(self, schema):
        # type: (str) -> str
        return hashlib.sha256(self.schema_to_string(schema).encode()).hexdigest()

    def schema_to_string(self, schema):
        # type: (dict) -> str
        return json.dumps(schema, sort_keys=True)

    def _check_stored_compatibility(self, old, schema):
        changeable_keywords = self.ignored_keywords
        if old:
            old_schema = json.loads(old['schema'])
            changes = list(itertools.islice(dictdiffer.diff(old_schema, schema['schema'], ignore=changeable_keywords, expand=True), 5))
            compatible = len(changes) == 0
        else:
            compatible = True
            changes = None
        if not compatible:
            err_str = "The new schema is not compatible with the old version that was already registered."
            err_str += " Incompatible changes were:\n"
            for c in changes:
                if c[0] == 'change':
                    err_str += '\t- Changed value "{}" from "{}" to "{}"\n'.format(c[1], c[2][0], c[2][1])
                if c[0] == 'add':
                    from_str = '.{}'.format(c[2][0][0]) if c[1] else c[2][0][0]
                    err_str += '\t- Added "{}{}" with value "{}"\n'.format(c[1], from_str, c[2][0][1])
                if c[0] == 'remove':
                    from_str = '.{}'.format(c[2][0][0]) if c[1] else c[2][0][0]
                    err_str += '\t- Removed "{}{}" with value "{}"\n'.format(c[1], from_str, c[2][0][1])

            raise SchemaException(err_str)

    @chainable
    def _upload_new_schema(self, claims, component, hash, name, schema, schema_str, vendor, version):

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
            old = yield self.find_latest(vendor, component, name, version)
            self._check_stored_compatibility(old, schema)

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
                        'createdAt': utc.now(),
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
                'build': len(updated['builds']),
                'schema': schema_str,
                'updatedAt': utc.now()
            }, upsert=True)