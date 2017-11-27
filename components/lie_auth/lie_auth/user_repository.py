from uuid import uuid4

import dictdiffer
import pytz

from mdstudio.db.connection import ConnectionType
from mdstudio.db.fields import timestamp_properties
from mdstudio.db.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.utc import now


def random_uuid():
    return str(uuid4())


def dict_property(name, property_class=None):
    if property_class is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            res = self[name]
            res.__class__ = property_class
            return res

    def setter(self, value):
        self[name] = value

    return property(getter, setter)


def dict_array_property(name, item_class=None):
    if item_class is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            for item in self[name]:
                item.__class__ = item_class
                yield item

    def setter(self, value):
        self[name] = value

    return property(getter, setter)


class DictWithTimestamps(dict):
    def __init__(self, created_at=None, updated_at=None, deleted_at=None, **kwargs):
        super(DictWithTimestamps, self).__init__(**kwargs)
        created_at = created_at or kwargs.get('createdAt', None)
        updated_at = updated_at or kwargs.get('updatedAt', None)
        deleted_at = deleted_at or kwargs.get('deletedAt', None)

        if created_at is not None:
            self.created_at = created_at
            if updated_at is None:
                self.updated_at = updated_at

        if updated_at is not None:
            self.updated_at = None

        if deleted_at is not None:
            self.deleted_at = deleted_at

    created_at = dict_property('createdAt')
    updated_at = dict_property('updatedAt')
    deleted_at = dict_property('deletedAt')


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
        date_time_fields = timestamp_properties()

    class Sessions(Model):
        connection_type = ConnectionType.User

    class Group(DictWithTimestamps):
        class Role(DictWithTimestamps):
            class Owner(DictWithTimestamps):
                handle = dict_property('handle')

                def __init__(self, handle, **kwargs):
                    super(UserRepository.Group.Role.Owner, self).__init__(**kwargs)
                    self.handle = handle

            class Permissions(dict):
                component_permissions = dict_property('componentPermissions')
                role_resource_permissions = dict_property('roleResourcePermissions')
                group_resource_permissions = dict_property('groupResourcePermissions')

                def __init__(self, component_permissions=None, role_resource_permissions=None, group_resource_permissions=None,
                             **kwargs):
                    super(UserRepository.Group.Role.Permissions, self).__init__(**kwargs)
                    self.component_permissions = component_permissions or kwargs.get('componentPermissions', None)
                    self.role_resource_permissions = role_resource_permissions or kwargs.get('roleResourcePermissions', None)
                    self.group_resource_permissions = group_resource_permissions or kwargs.get('groupResourcePermissions', None)

            name = dict_property('roleName')
            owners = dict_array_property('owners', Owner)
            permissions = dict_property('permissions', Permissions)

            def __init__(self, name=None, handle=None, owners=None, permissions=None, **kwargs):
                super(UserRepository.Group.Role, self).__init__(**kwargs)
                self.name = name or kwargs.get('roleName')
                self.handle = handle
                self.owners = owners
                self.permissions = permissions

        class Member(DictWithTimestamps):
            handle = dict_property('handle')
            roles = dict_property('roles')

            def __init__(self, handle=None, roles=None, **kwargs):
                super(UserRepository.Group.Member, self).__init__(**kwargs)
                self.handle = handle
                self.roles = roles

        class Component(DictWithTimestamps):
            name = dict_property('componentName')
            handle = dict_property('handle')
            owner_roles = dict_property('owner_roles')

            def __init__(self, name=None, handle=None, owner_roles=None, **kwargs):
                super(UserRepository.Group.Component, self).__init__(**kwargs)
                self.name = name or kwargs.get('componentName', None)
                self.handle = handle
                self.owner_roles = owner_roles or kwargs.get('ownerRoles')

        def __init__(self, name=None, display_name=None, handle=None, roles=None, members=None, components=None, **kwargs):
            super(UserRepository.Group, self).__init__(**kwargs)
            self.name = name or kwargs.get('groupName', None)
            self.display_name = display_name or kwargs.get('displayName', None)
            self.handle = handle
            self.roles = roles
            self.members = members
            self.components = components

        name = dict_property('groupName')
        display_name = dict_property('displayName')
        handle = dict_property('handle')
        roles = dict_array_property('roles', Role)
        members = dict_array_property('members', Member)
        components = dict_array_property('components', Component)

    class Groups(Model):
        """
        {
            'groupName': <groupName>,
            'displayName': <displayName>,
            'handle': <handle>,
            'roles': [
                {
                    'roleName': <roleName>,
                    'owners': [<userHandle>],
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
                    'componentName': <componentName>,
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
        date_time_fields = timestamp_properties(['', 'roles', 'roles.owners', 'members', 'components'])

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

        created_at = now()

        user = self._with_create_time({
            'username': username,
            'displayName': display_name,
            'handle': random_uuid(),
            'password': password_hash,
            'email': email,
            'timezone': pytz.utc.zone
        }, created_at=created_at)

        inserted = yield self.users.find_one_and_update({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        }, {
            '$setOnInsert': user
        }, upsert=True, projection={'_id': False}, return_updated=True)

        return_value(user if user == inserted else None)

    def find_user(self, username=None, handle=None, email=None):
        user_filter = self._add_to_request({}, username=username, handle=handle, email=email)

        assert user_filter, "You need at least one of [username, handle, email]"

        user_filter['deletedAt'] = {'$exists': False}

        return self.users.find_one(user_filter, {'_id': False, 'password': False})

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
    @chainable
    def create_group(self, group_name, owner_handle, display_name=None):
        if display_name is None:
            display_name = group_name

        created_at = now()
        role_uiid = random_uuid()

        group_role_owner = UserRepository.Group.Role.Owner(owner_handle, created_at=created_at)
        initial_permissions = UserRepository.Group.Role.Permissions([], True, True, created_at=created_at)
        initial_role = UserRepository.Group.Role('owner', role_uiid, [group_role_owner], initial_permissions, created_at=created_at)

        group = UserRepository.Group(group_name, display_name, random_uuid(), [initial_role], UserRepository.Group.Member(owner_handle, [role_uiid]), [], created_at=created_at)

        # group = self._with_create_time({
        #     'groupName': group_name,
        #     'displayName': display_name,
        #     'handle': random_uuid(),
        #     'roles': [
        #         self._with_create_time({
        #             'role': 'owner',
        #             'owners': [owner_handle],
        #             'handle': role_uiid,
        #             'members': [
        #                 self._with_create_time({
        #                     'handle': owner_handle
        #                 }, created_at)
        #             ],
        #             'permissions': {
        #                 'componentPermissions': [],
        #                 'roleResourcePermissions': True,
        #                 'groupResourcePermissions': True
        #             }
        #         }, created_at)
        #     ],
        #     'members': [
        #         self._with_create_time({
        #             'handle': owner_handle,
        #             'roles': [role_uiid]
        #         }, created_at)
        #     ],
        #     'components': []
        # }, created_at)

        print(group)

        inserted = yield self.groups.find_one_and_update({
            'groupName': group_name
        }, {
            '$setOnInsert': group
        }, upsert=True, projection={'_id': False}, return_updated=True)

        print([p for p in dictdiffer.diff(group, inserted)])

        return_value(group if group == inserted else None)

    def create_group_role(self, group_name, role_name, owner_handle, role_resources=True, group_resources=False):
        created_at = now()

        group_filter = {
            'groupName': group_name,
            'roles': {
                '$not': {
                    '$elemMatch': {
                        'role': role_name
                    }
                }
            }
        }

        role_owner = UserRepository.Group.Role.Member(owner_handle, created_at=created_at)
        initial_permissions = UserRepository.Group.Role.Permissions([], role_resources, group_resources, created_at=created_at)

        group_update = {
            '$push': {
                'roles': UserRepository.Group.Role(role_name, role_owner, role_owner, initial_permissions, created_at=created_at)
            }
            #     {
            #     'roles': self._with_create_time({
            #         'role': role_name,
            #         'owners': [user_handle],
            #         'members': [
            #             self._with_create_time({
            #                 'handle': user_handle
            #             }, created_at)
            #         ],
            #         'permissions': {
            #             'componentPermissions': [],
            #             'roleResourcePermissions': role_resources if role_resources else [],
            #             'groupResourcePermissions': group_resources if group_resources else []
            #         }
            #     })
            # }
        }

        return (yield self.groups.find_one_and_update(group_filter, group_update, {'_id': False}, return_updated=True))

    def add_group_member(self, group_name, role_handle, user_handle):
        created_at = now()

        group_filter = {
            'groupName': group_name,
            'members': {
                '$not': {
                    '$elemMatch': {
                        'handle': user_handle
                    }
                }
            }
        }

        group_update = {
            '$push': {
                'members': {
                    UserRepository.Group.Member(user_handle, [role_handle], created_at=created_at)
                },
            }
        }

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
