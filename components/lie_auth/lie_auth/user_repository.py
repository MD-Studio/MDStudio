from uuid import uuid4 as random_uuid

import pytz

from mdstudio.db.connection import ConnectionType
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.utc import now


class UserRepository(object):
    class Users(Model):
        """
        {
            'username': <username>,
            'displayName': <displayName>,
            'handle': <handle>,
            'password': <hashedPassword>,
            'email': <encryptedEmail>,
            'timezone': <timezone>,
            'createdAt': <createdAt>,
            'updatedAt': <updatedAt>,
            'deletedAt': <deletedAt>
        }
        """
        connection_type = ConnectionType.User

        encrypted_fields = ['email']
        date_time_fields = ['updatedAt', 'createdAt', 'deletedAt']

    class Sessions(Model):
        connection_type = ConnectionType.User

    class Groups(Model):
        """
        {
            'groupName': <groupName>,
            'displayName': <displayName>,
            'handle': <handle>,
            'roles': [
                {
                    'role': <roleName>,
                    'owners': [<userHandle>],
                    'members': [<userHandle>],
                    'permissions': {
                        'componentPermissions': [ $componentPermission$ ],
                        'roleResourcePermissions': {
                            'oneOf': [
                                $componentPermissions$,
                                <bool>
                            ]
                        },
                        groupResourcePermissions': {
                            'oneOf': [
                                $componentPerissions$,
                                <bool>
                            ]
                        }
                    }
                }
            },
            'members': [
                {
                    'handle': <userHandle>,
                    'roles': [<roleName>],
                    'createdAt': <createdAt>,
                    'updatedAt': <updatedAt>
                }
            ],
            'components': [
                {
                    'component': <component>,
                    'handle': <handle>
                    'ownerRoles': [<roleName>],
                    'createdAt': <createdAt>,
                    'updatedAt': <updatedAt>
                }
            ],
            'createdAt': <createdAt>,
            'updatedAt': <updatedAt>,
            'deletedAt': <deletedAt>
        }

        $roleMemberPermissions$: {
            'handle': <userHandle>,
            'roleResourcePermissions': [ $componentPermissions$ ]
        }


        $componentPermision$: {
            'handle': <handle>,
            'manage': <bool>,
            'remove': <bool>,
            'namespace': [<action>],
            'scopes': [
                {
                    'scope': <scopeName>,
                    'actions': [<action>]
                }
            ],
            'endpoints': [
                {
                    'endpoint': <endpoint>,
                    'actions': [<action>]
                }
            ]
        }



                        'addMember': {
                            'oneOf': [
                                [<roles>],
                                <bool>
                            ]
                        }
                        'removeMember': {
                            'oneOf': [
                                [<roles>],
                                <bool>
                            ]
                        },
                        'addRoles': <bool>,
                        'removeRoles': <bool>,
                        'manageRoles': {
                            'oneOf': [
                                {
                                    'role': <roleName>,
                                    'remove': <bool>
                                },
                                <bool>
                            ]
                        },
                        'addComponents': <bool>,
                        'removeComponents': <bool>
        """
        connection_type = ConnectionType.User

    def __init__(self, db_wrapper):
        self.wrapper = db_wrapper

    @property
    def users(self):
        return self.Users(self.wrapper)

    """
    User CRUD
    """
    @chainable
    def create_user(self, username, password_hash, email, display_name=None):
        if display_name is None:
            display_name = username

        user = self._with_create_time({
            'username': username,
            'displayName': display_name,
            'handle': random_uuid(),
            'password': password_hash,
            'email': email,
            'timezone': pytz.utc.tzname()
        })

        inserted = yield self.users.find_one_and_update({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        }, {
            '$setOnInsert': user
        }, upsert=True, projection={'_id': 0}, return_updated=True)

        return_value(user == inserted)

    def find_user(self, username=None, handle=None, email=None):
        user_filter = self._add_to_request({}, username=username, handle=handle, email=email)

        assert user_filter, "You need at least one of [username, handle, email]"

        user_filter['deletedAt'] = {'$exists': False}

        return self.users.find_one(user_filter, {'_id': 0, 'password': 0})

    @chainable
    def update_user(self, handle, **kwargs):
        update_user = self._add_to_request({}, ['display_name', 'email', 'password', 'timezone'], **kwargs)

        assert update_user, 'You need to provide at least one property to update'

        update_user['updatedAt'] = now()

        return_value((yield self.users.update_one({'handle': handle}, update_user).modified) == 1)

    @chainable
    def deactivate_user(self, handle):
        modified = self.users.update_one({'handle': handle}, {'deletedAt': now()}).modified

        return_value(modified == 1)

    @chainable
    def check_user_password(self, username, password):
        return_value((yield self.find_user(username=username)['password']) == password)

    @staticmethod
    def _add_to_request(request, accepted_parameters, **kwargs):
        for p in accepted_parameters:
            value = kwargs.pop(p, None)
            if value:
                request[p] = value

        assert len(kwargs.items()) == 0, 'Provided invalid parameters: {}'.format(kwargs.keys())

        return request

    """
    Group CRUD
    """
    def create_group(self, group_name, owner_handle, display_name=None):
        if display_name is None:
            display_name = group_name

        created_at = now()

        group = self._with_create_time({
            'groupName': group_name,
            'displayName': display_name,
            'handle': random_uuid(),
            'roles': [
                self._with_create_time({
                    'role': 'owner',
                    'owners': [owner_handle],
                    'members': [
                        self._with_create_time({
                            'handle': owner_handle
                        }, created_at)
                    ],
                    'permissions': {
                        'componentPermissions': [],
                        'roleResourcePermissions': True,
                        'groupResourcePermissions': True
                    }
                }, created_at)
            ],
            'members': [
                self._with_create_time({
                    'handle': owner_handle,
                    'roles': ['owner']
                }, created_at)
            ],
            'components': []
        }, created_at)

        inserted = yield self.groups.find_one_and_update({
            'groupName': group_name
        }, {
            '$setOnInsert': group
        }, upsert=True, projection={'_id': 0}, return_updated=True)

        return_value(group == inserted)

    def create_group_role(self, group_name, role_name, user_handle, role_resources=True, group_resources=False):
        created_at = now()

        group_filter = {
            'groupName': group_name,
            'roles': {
                '$not': {
                    '$elemMatch': {}
                }
            }
        }

        group_update = {
            '$push': {
                'roles': self._with_create_time({
                    'role': role_name,
                    'owners': [user_handle],
                    'members': [
                        self._with_create_time({
                            'handle': user_handle
                        }, created_at)
                    ],
                    'permissions': {
                        'componentPermissions': [],
                        'roleResourcePermissions': role_resources if role_resources else [],
                        'groupResourcePermissions': group_resources if group_resources else []
                    }
                })
            }
        }

        return_value((yield self.groups.update_one({'groupName': group_name}, group_update).modified) == 1)

    @staticmethod
    def _with_create_time(entry, created_at=None):
        if created_at is None:
            created_at = now()

        entry['createdAt'] = created_at
        entry['updatedAt'] = created_at

        return entry

    @property
    def sessions(self):
        return self.Sessions(self.wrapper)

    @property
    def groups(self):
        return self.Groups(self.wrapper)

