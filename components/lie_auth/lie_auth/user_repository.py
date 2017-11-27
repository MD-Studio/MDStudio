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


def dict_property(name, modifier=None):
    if modifier is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            return modifier(self[name])

    def setter(self, value):
        self[name] = value

    return property(getter, setter)


def dict_array_property(name, modifier=None):
    if modifier is None:
        def getter(self):
            return self[name]
    else:
        def getter(self):
            for item in self[name]:
                yield modifier(item)

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
                self.updated_at = created_at

        if updated_at is not None:
            self.updated_at = None

        if deleted_at is not None:
            self.deleted_at = deleted_at

    created_at = dict_property('createdAt')
    updated_at = dict_property('updatedAt')
    deleted_at = dict_property('deletedAt')

    @classmethod
    def from_dict(cls, instance):
        inst = cls()
        inst.update(instance)
        return inst


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

        class Instance(DictWithTimestamps):
            name = dict_property('username')
            username = dict_property('username')
            display_name = dict_property('displayName')
            handle = dict_property('handle')
            password = dict_property('password')
            email = dict_property('email')
            timezone = dict_property('timezone')

    class Sessions(Model):
        connection_type = ConnectionType.User

    class Group(DictWithTimestamps):
        class Role(DictWithTimestamps):
            class Member(DictWithTimestamps):
                handle = dict_property('handle')

                def __init__(self, handle, **kwargs):
                    super(UserRepository.Group.Role.Member, self).__init__(**kwargs)
                    self.handle = handle

            class Permissions(dict):
                class ComponentPermission(DictWithTimestamps):
                    handle = dict_property('handle')
                    namespace = dict_property('namespace')
                    scopes = dict_array_property('scopes')
                    endpoints = dict_array_property('endpoints')

                    def __init__(self, handle=None, namespace=None, scopes=None, endpoints=None, **kwargs):
                        super(UserRepository.Group.Role.Permissions.ComponentPermission, self).__init__(**kwargs)
                        self.handle = handle
                        self.namespace = namespace
                        self.scopes = scopes
                        self.endpoints = endpoints

                @classmethod
                def from_dict(cls, instance):
                    inst = cls()
                    inst.update(instance)
                    return inst

                component_permissions = dict_array_property('componentPermissions', ComponentPermission.from_dict)
                role_resource_permissions = dict_array_property('roleResourcePermissions', ComponentPermission.from_dict)
                group_resource_permissions = dict_array_property('groupResourcePermissions', ComponentPermission.from_dict)

                def __init__(self, component_permissions=None, role_resource_permissions=None, group_resource_permissions=None, **kwargs):
                    super(UserRepository.Group.Role.Permissions, self).__init__(**kwargs)
                    self.component_permissions = component_permissions or kwargs.get('componentPermissions', [])
                    self.role_resource_permissions = role_resource_permissions or kwargs.get('roleResourcePermissions', False)
                    self.group_resource_permissions = group_resource_permissions or kwargs.get('groupResourcePermissions', False)

            name = dict_property('roleName')
            handle = dict_property('handle')
            owners = dict_array_property('owners', Member.from_dict)
            members = dict_array_property('members', Member.from_dict)
            permissions = dict_property('permissions', Permissions.from_dict)

            def __init__(self, name=None, handle=None, owners=None, members=None, permissions=None, **kwargs):
                super(UserRepository.Group.Role, self).__init__(**kwargs)
                self.name = name or kwargs.get('roleName')
                self.handle = handle
                self.owners = owners
                self.members = members
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
        roles = dict_array_property('roles', Role.from_dict)
        members = dict_array_property('members', Member.from_dict)
        components = dict_array_property('components', Component.from_dict)

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
        date_time_fields = timestamp_properties([
            '',
            'roles',
            'roles.owners',
            'roles.members',
            'role.permissions.componentPermissions',
            'role.permissions.groupResourcePermissions',
            'role.permissions.roleResourcePermissions',
            'members',
            'components'
        ])

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

        return_value(UserRepository.Users.Instance.from_dict(user) if user == inserted else None)

    @chainable
    def find_user(self, username=None, handle=None, email=None):
        # type: (Optional[str], Optional[str], Optional[str]) -> UserRepository.Users.Instance
        user_filter = self._add_to_request({}, ['username', 'handle', 'email'], username=username, handle=handle, email=email)

        assert user_filter, "You need at least one of [username, handle, email]"

        user_filter['deletedAt'] = {'$exists': False}

        result = yield self.users.find_one(user_filter, {'_id': False, 'password': False})

        if isinstance(result, dict):
            result = UserRepository.Users.Instance.from_dict(result)

        return_value(result)

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
        return_value((yield self.find_user(username=username).password) == password)

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
    def create_group(self, group_name, owner_username, display_name=None):
        if display_name is None:
            display_name = group_name

        created_at = now()
        role_uiid = random_uuid()

        owner_handle = (yield self.find_user(username=owner_username).handle)

        role_owner = UserRepository.Group.Role.Member(owner_handle, created_at=created_at)
        initial_permissions = UserRepository.Group.Role.Permissions([], True, True)
        initial_role = UserRepository.Group.Role('owner', role_uiid, [role_owner], [role_owner], initial_permissions, created_at=created_at)
        initial_member = UserRepository.Group.Member(owner_handle, [role_uiid], created_at=created_at)

        group = UserRepository.Group(group_name, display_name, random_uuid(), [initial_role], [initial_member], [], created_at=created_at)

        inserted = yield self.groups.find_one_and_update({
            'groupName': group_name
        }, {
            '$setOnInsert': group
        }, upsert=True, projection={'_id': False}, return_updated=True)

        return_value(UserRepository.Group.from_dict(group) if group == inserted else None)

    @chainable
    def create_group_role(self, group_name, role_name, owner_username, role_resources=True, group_resources=False):
        created_at = now()

        owner_handle = (yield self.find_user(username=owner_username).handle)

        group_filter = {
            'groupName': group_name,
            'roles': {
                '$not': {
                    '$elemMatch': {
                        'role': role_name
                    }
                }
            },
            'members': {
                '$elemMatch': {
                    'handle': owner_handle
                }
            }
        }

        role_uuid = random_uuid()
        role_owner = UserRepository.Group.Role.Member(owner_handle, created_at=created_at)
        initial_permissions = UserRepository.Group.Role.Permissions([], role_resources, group_resources, created_at=created_at)

        group_update = {
            '$push': {
                'roles': UserRepository.Group.Role(role_name, role_uuid, [role_owner], [role_owner], initial_permissions),
                'members.$.roles': role_uuid
            }
        }

        updated = yield self.groups.find_one_and_update(group_filter, group_update, projection={'roles': {'$elemMatch': {'handle': role_uuid}}}, return_updated=True).get('roles', [None])[0]

        return_value(UserRepository.Group.Role.from_dict(updated) if updated is not None and updated['handle'] == role_uuid else None)

    @chainable
    def find_role(self, group_name, role_name):
        # type: (str, str) -> UserRepository.Group.Role
        role_filter = {
            'groupName': group_name,
            'roles': {
                '$elemMatch': {
                    'roleName': role_name
                }
            }
        }

        role = yield self.groups.find_one(role_filter, projection={'roles': {'$elemMatch': {'roleName': role_name}}}).get('roles', [None])[0]

        return_value(UserRepository.Group.Role.from_dict(role) if role else None)

    @chainable
    def add_group_member(self, group_name, role_name, username):
        created_at = now()

        user_handle = yield self.find_user(username=username).handle
        role_handle = yield self.find_role(group_name, role_name).handle

        group_filter = {
            'groupName': group_name,
            'members': {
                '$not': {
                    '$elemMatch': {
                        'handle': user_handle
                    }
                }
            },
            'roles': {
                '$elemMatch': {
                    'handle': role_handle
                }
            }
        }

        group_update = {
            '$push': {
                'members': UserRepository.Group.Member(user_handle, [role_handle], created_at=created_at),
                'roles.$.members': UserRepository.Group.Role.Member(user_handle, created_at=created_at)
            }
        }

        updated = yield self.groups.update_one(group_filter, group_update).modified

        return_value(updated == 1)

    @chainable
    def add_role_member(self, group_name, role_name, username):
        created_at = now()

        user_handle = yield self.find_user(username=username).handle

        group_filter = {
            'groupName': group_name,
            'members': {
                '$elemMatch': {
                    'handle': user_handle
                }
            },
            'roles': {
                '$elemMatch': {
                    'roleName': role_name
                }
            }
        }

        group_update = {
            '$push': {
                'roles.$.members': UserRepository.Group.Role.Member(user_handle, created_at=created_at)
            }
        }

        updated = yield self.groups.update_one(group_filter, group_update).modified

        return_value(updated == 1)

    @chainable
    def create_component(self, group_name, role_name, component_name):
        created_at = now()
        component_handle = random_uuid()

        role_handle = yield self.find_role(group_name, role_name).handle

        component_filter = {
            'groupName': group_name,
            'roles': {
                '$elemMatch': {
                    'handle': role_handle
                }
            },
            'components': {
                '$not': {
                    '$elemMatch': {
                        'componentName': component_name
                    }
                }
            }
        }

        group_update = {
            '$push': {
                'roles.$.permissions.componentPermissions': UserRepository.Group.Role.Permissions.ComponentPermission(component_handle, True, True, True, created_at=created_at),
                'components': UserRepository.Group.Component(component_name, component_handle, [role_handle], created_at=created_at)
            }
        }

        return_value((yield self.groups.find_one_and_update(component_filter, group_update, projection={
            'components': {
                '$elemMatch': {
                    'componentName': component_name
                }
            }
        }, return_updated=True).get('components', [None])[0]))

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
