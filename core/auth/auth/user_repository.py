import itertools

import os
import pytz
from copy import deepcopy
from enum import Enum

from mdstudio.collection import dict_property, dict_array_property
from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.fields import timestamp_properties, Fields
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.service.model import Model
from mdstudio.utc import now
from mdstudio.util.random import random_uuid


class ModelInstance(dict):
    @classmethod
    def from_dict(cls, instance):
        inst = cls()
        inst.update(instance or {})
        return inst


class InstanceWithTimestamps(ModelInstance):
    def __init__(self, created_at=None, updated_at=None, deleted_at=None, **kwargs):
        super(InstanceWithTimestamps, self).__init__(**kwargs)
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

class PermissionType(Enum):
    ComponentNamespace = 0
    NamedScope = 1
    SpecificEndpoint = 2
    FullAccess = 3


class UserRepository(object):
    _CLIENT_ID_CHARACTER_SET = r'!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}'

    class Users(Model):
        connection_type = ConnectionType.User

        encrypted_fields = ['email', 'authentication.storedKey', 'authentication.serverKey', 'authentication.salt']
        date_time_fields = timestamp_properties()

        class Instance(InstanceWithTimestamps):
            name = dict_property('username')
            username = dict_property('username')
            display_name = dict_property('displayName')
            handle = dict_property('handle')
            authentication = dict_property('authentication')
            email = dict_property('email')
            timezone = dict_property('timezone')

    class Sessions(Model):
        connection_type = ConnectionType.User

    class Clients(Model):
        connection_type = ConnectionType.User

        date_time_fields = timestamp_properties([
            '',
            {
                'groups': [
                    '',
                    'roles'
                ]
            }
        ])

        class Instance(InstanceWithTimestamps):
            class Group(InstanceWithTimestamps):
                class Role(InstanceWithTimestamps):
                    class Permission(InstanceWithTimestamps):
                        actions = dict_property('actions')

                        def __init__(self, actions=None, created_at=None):
                            self.actions = actions

                            super(UserRepository.Clients.Instance.Group.Role.Permission, self).__init__(created_at=created_at)

                    permissions = dict_property('permissions')

                    def __init__(self, permissions=None, created_at=None):
                        self.permissions = permissions

                        super(UserRepository.Clients.Instance.Group.Role, self).__init__(created_at=created_at)

                handle = dict_property('handle')
                roles = dict_property('roles')

                def __init__(self, handle=None, roles=None, created_at=None):
                    self.handle = handle
                    self.roles = roles

                    super(UserRepository.Clients.Instance.Group, self).__init__(created_at=created_at)

            handle = dict_property('handle')
            user = dict_property('userHandle')
            authentication = dict_property('authentication')
            groups = dict_array_property('groups', Group)

            def __init__(self, handle=None, user=None, groups=None, created_at=None, **kwargs):
                self.handle = handle
                self.user = user
                self.groups = groups

                super(UserRepository.Clients.Instance, self).__init__(created_at=created_at)


    class Groups(Model):
        connection_type = ConnectionType.User
        date_time_fields = timestamp_properties([
            '',
            {
                'roles': [
                    '',
                    'owners',
                    'members'
                ]
            },
            'members',
            'components'
        ])

        class Instance(InstanceWithTimestamps):
            class Role(InstanceWithTimestamps):
                class Member(InstanceWithTimestamps):
                    handle = dict_property('handle')

                    def __init__(self, handle, **kwargs):
                        super(UserRepository.Groups.Instance.Role.Member, self).__init__(**kwargs)
                        self.handle = handle

                class Permissions(ModelInstance):
                    class ComponentPermission(InstanceWithTimestamps):
                        namespace = dict_property('namespace')
                        full_namespace = dict_property('fullNamespace')
                        scopes = dict_array_property('scopes')
                        endpoints = dict_array_property('endpoints')

                        def __init__(self, full_namespace=False, namespace=None, scopes=None, endpoints=None, **kwargs):
                            super(UserRepository.Groups.Instance.Role.Permissions.ComponentPermission, self).__init__(**kwargs)
                            self.full_namespace = full_namespace
                            self.namespace = namespace or []
                            self.scopes = scopes or {}
                            self.endpoints = endpoints or {}

                    component_permissions = dict_property('componentPermissions')
                    role_resource_permissions = dict_property('roleResourcePermissions')
                    group_resource_permissions = dict_property('groupResourcePermissions')

                    def __init__(self, component_permissions=None, role_resource_permissions=None, group_resource_permissions=None, **kwargs):
                        super(UserRepository.Groups.Instance.Role.Permissions, self).__init__(**kwargs)
                        self.component_permissions = component_permissions or kwargs.get('componentPermissions', {})
                        self.role_resource_permissions = role_resource_permissions or kwargs.get('roleResourcePermissions', {})
                        self.group_resource_permissions = group_resource_permissions or kwargs.get('groupResourcePermissions', {})

                name = dict_property('roleName')
                handle = dict_property('handle')
                owners = dict_array_property('owners', Member.from_dict)
                members = dict_array_property('members', Member.from_dict)
                permissions = dict_property('permissions', Permissions.from_dict)

                def __init__(self, name=None, handle=None, owners=None, members=None, permissions=None, **kwargs):
                    super(UserRepository.Groups.Instance.Role, self).__init__(**kwargs)
                    self.name = name or kwargs.get('roleName')
                    self.handle = handle
                    self.owners = owners
                    self.members = members
                    self.permissions = permissions

            class Member(InstanceWithTimestamps):
                handle = dict_property('handle')
                roles = dict_property('roles')

                def __init__(self, handle=None, roles=None, **kwargs):
                    super(UserRepository.Groups.Instance.Member, self).__init__(**kwargs)
                    self.handle = handle
                    self.roles = roles

            class Component(InstanceWithTimestamps):
                name = dict_property('componentName')
                handle = dict_property('handle')
                owner_roles = dict_property('owner_roles')

                def __init__(self, name=None, owner_roles=None, **kwargs):
                    super(UserRepository.Groups.Instance.Component, self).__init__(**kwargs)
                    self.name = name or kwargs.get('componentName', None)
                    self.owner_roles = owner_roles or kwargs.get('ownerRoles')

            def __init__(self, name=None, display_name=None, handle=None, roles=None, members=None, components=None, **kwargs):
                super(UserRepository.Groups.Instance, self).__init__(**kwargs)
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

    def __init__(self, db_wrapper):
        self.wrapper = db_wrapper

    @property
    def users(self):
        return self.Users(self.wrapper)

    """
    User CRUD
    """

    @chainable
    def create_user(self, username, authentication, email, display_name=None):
        if display_name is None:
            display_name = username

        created_at = now()

        user = self._with_create_time({
            'username': username,
            'displayName': display_name,
            'handle': random_uuid(),
            'authentication': authentication,
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
    def find_user(self, username=None, handle=None, email=None, with_authentication=False):
        # type: (Optional[str], Optional[str], Optional[str]) -> UserRepository.Users.Instance
        user_filter = self._add_to_request({}, ['username', 'handle', 'email'], username=username, handle=handle, email=email)

        assert user_filter, "You need at least one of [username, handle, email]"

        user_filter['deletedAt'] = {'$exists': False}

        result = yield self.users.find_one(user_filter, {'_id': False, 'authentication': with_authentication})

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

        owner_handle = yield self.find_user(username=owner_username).handle

        _Group = UserRepository.Groups.Instance

        role_owner = _Group.Role.Member(owner_handle, created_at=created_at)
        initial_permissions = _Group.Role.Permissions()
        initial_role = _Group.Role('owner', role_uiid, [role_owner], [role_owner], initial_permissions, created_at=created_at)
        initial_member = _Group.Member(owner_handle, [role_uiid], created_at=created_at)

        group = _Group(group_name, display_name, random_uuid(), [initial_role], [initial_member], [], created_at=created_at)

        inserted = yield self.groups.find_one_and_update({
            'groupName': group_name
        }, {
            '$setOnInsert': group
        }, upsert=True, projection={'_id': False}, return_updated=True)

        return_value(_Group.from_dict(group) if group == inserted else None)

    @chainable
    def find_group(self, group_name):
        group = yield self.groups.find_one({'groupName': group_name}, {'_id': False})

        return_value(UserRepository.Groups.Instance.from_dict(group) if group else None)

    @chainable
    def check_membership(self, username, group_name, group_role=None):
        user_handle = yield self.find_user(username).handle

        group_filter = {
            'groupName': group_name,
            'members': {
                '$elemMatch': {
                    'handle': user_handle
                }
            }
        }

        if group_role is not None:
            group_filter['roles'] = {
                '$elemMatch': {
                    'roleName': group_role,
                    'members': {
                        '$elemMatch': user_handle
                    }
                }
            }

        group = yield self.groups.find_one(group_filter)

        return_value(group is not None)

    @chainable
    def check_permission(self, username, group_name, component, uri, action, role_name=None):
        # @todo: check
        user_handle = yield self.find_user(username).handle

        roles_filter = {
            'groupName': group_name,
            'members': {
                '$elemMatch': {
                    'handle': user_handle
                }
            },
            'roles': {
                '$elemMatch': {
                    'members': {
                        '$elemMatch': {
                            'handle': user_handle
                        }
                    },
                    'permissions.componentPermissions.{}'.format(component): {
                        '$exists': True
                    }
                }
            },
            'components': {
                '$elemMatch': {
                    'componentName': component
                }
            }
        }

        if role_name:
            roles_filter['roles']['$elemMatch']['roleName'] = role_name

        _Group = UserRepository.Groups.Instance

        # @todo: subgroups
        group = yield self.groups.find_one(roles_filter, fields=self._group_permission_timestamps('componentPermissions', component))\
                                 .transform(UserRepository.Groups.Instance.from_dict)  # type: _Group

        permission = False

        if not group:
            return_value(False)

        for role in group.roles:  # type: _Group.Role
            if component in role.permissions.component_permissions:
                permissions = _Group.Role.Permissions.ComponentPermission.from_dict(role.permissions.component_permissions.get(component))

                # @todo: check if endpoint is in named scope
                if permissions.full_namespace:
                    permission = True
                elif any(v in permissions.namespace for v in itertools.chain(action, '*')):
                    permission = True
                elif any(v in permissions.endpoints.get(uri, []) for v in itertools.chain(action, '*')):
                    permission = True

        return_value(permission)

    @chainable
    def create_group_role(self, group_name, role_name, owner_username, role_resources=None, group_resources=None):
        created_at = now()

        owner_handle = (yield self.find_user(username=owner_username).handle)

        group_filter = {
            'groupName': group_name,
            'roles': {
                '$not': {
                    '$elemMatch': {
                        'roleName': role_name
                    }
                }
            },
            'members': {
                '$elemMatch': {
                    'handle': owner_handle
                }
            }
        }

        _Group = UserRepository.Groups.Instance

        role_uuid = random_uuid()
        role_owner = _Group.Role.Member(owner_handle, created_at=created_at)
        initial_permissions = _Group.Role.Permissions(role_resource_permissions=role_resources, group_resource_permissions=group_resources, created_at=created_at)

        group_update = self._group_update_times({
            '$push': {
                'roles': _Group.Role(role_name, role_uuid, [role_owner], [role_owner], initial_permissions, created_at=created_at),
                'members.$.roles': role_uuid
            }
        }, created_at)

        updated = yield self.groups.find_one_and_update(group_filter, group_update, projection={'roles': {'$elemMatch': {'handle': role_uuid}}}, return_updated=True).transform(self._extract_role)

        return_value(_Group.Role.from_dict(updated) if updated is not None and updated['handle'] == role_uuid else None)

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

        role = yield self.groups.find_one(role_filter, projection={
            'roles': {
                '$elemMatch': {
                    'roleName': role_name
                }
            }
        }).transform(self._extract_role)

        return_value(UserRepository.Groups.Instance.Role.from_dict(role) if role else None)

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

        group_update = self._role_update_times({
            '$push': {
                'members': UserRepository.Groups.Instance.Member(user_handle, [role_handle], created_at=created_at),
                'roles.$.members': UserRepository.Groups.Instance.Role.Member(user_handle, created_at=created_at)
            }
        }, created_at)

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

        group_update = self._role_update_times({
            '$push': {
                'roles.$.members': UserRepository.Groups.Instance.Role.Member(user_handle, created_at=created_at)
            }
        }, created_at)

        updated = yield self.groups.update_one(group_filter, group_update).modified

        return_value(updated == 1)

    @chainable
    def create_component(self, group_name, role_name, component_name):
        created_at = now()
        fields = self._group_permission_timestamps('componentPermissions', component_name)

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

        _Group = UserRepository.Groups.Instance

        group_update = self._role_update_times({
            '$push': {
                'components': _Group.Component(component_name, [role_handle], created_at=created_at)
            },
            '$set': {
                'roles.$.permissions.componentPermissions.{}'.format(component_name):
                    _Group.Role.Permissions.ComponentPermission(True, created_at=created_at)
            }
        }, created_at)

        updated = yield self.groups.find_one_and_update(component_filter, group_update, projection={
            'components': {
                '$elemMatch': {
                    'componentName': component_name
                }
            }
        }, return_updated=True, fields=fields).transform(self._extract_group_component)

        return_value(_Group.Component.from_dict(updated) if updated else None)

    @chainable
    def find_component(self, group_name, component_name):
        component = yield self.groups.find_one({
            'groupName': group_name,
            'components': {
                '$elemMatch': {
                    'componentName': component_name
                }
            }
        }, {
            'components': {
                '$elemMatch': {
                    'componentName': component_name
                }
            }
        }).transform(self._extract_group_component)

        return_value(UserRepository.Groups.Instance.Component.from_dict(component) if component else None)

    @chainable
    def add_permission_rule(self, group_name, role_name, permission_set, component_name, permission_type, permission_actions=None, permission_scope_or_uri=None, full_namespace=False):
        _ComponentPermission = UserRepository.Groups.Instance.Role.Permissions.ComponentPermission

        created_at = now()
        fields = self._group_permission_timestamps(permission_set, component_name)
        permission_scope_or_uri = permission_scope_or_uri.replace('.', '/') if permission_scope_or_uri is not None else None

        if permission_actions is not None and not isinstance(permission_actions, list):
            permission_actions = [permission_actions]

        role_handle = yield self.find_role(group_name, role_name).handle

        component_match_filter = {
            'roles': {
                '$elemMatch': {
                    'handle': role_handle,
                    'permissions.{}.{}'.format(permission_set, component_name): {
                        '$exists': True
                    }
                }
            }
        }

        component_new_filter = {
            'roles': {
                '$elemMatch': {
                    'handle': role_handle,
                    'permissions.{}.{}'.format(permission_set, component_name): {
                        '$exists': False
                    }
                }
            }
        }

        if permission_set == 'componentPermissions':
            component_match_filter['components'] = component_new_filter['components'] = {
                '$elemMatch': {
                    'componentName': component_name
                }
            }

        component_rules = yield self.groups.find_one(component_match_filter, component_match_filter)

        # If no rule exists for this component under this role, create it
        if component_rules is None:
            component_permission = _ComponentPermission(False, created_at=created_at)
            if permission_type == PermissionType.ComponentNamespace:
                component_permission.namespace = permission_actions
            elif permission_type == PermissionType.NamedScope or permission_type == PermissionType.SpecificEndpoint:
                key = 'scopes' if permission_type == PermissionType.NamedScope else 'endpoints'
                component_permission[key] = {
                    permission_scope_or_uri: permission_actions
                }
            elif permission_type == PermissionType.FullAccess:
                component_permission.full_namespace = full_namespace
            else:
                raise NotImplementedError('Unknown permission type')

            role_update = self._role_update_times({
                '$set': {
                    self._role_permissions(permission_set, component_name): component_permission
                }
            }, created_at)

            updated = yield self.groups.find_one_and_update(component_new_filter, role_update, projection=component_match_filter, return_updated=True, fields=fields).transform(self._extract_component_permission, permission_set, component_name)

            return_value(updated is not None and updated['createdAt'] == created_at)
        else:
            if permission_type == PermissionType.ComponentNamespace:
                role_update = self._role_permission_update_times({
                    '$addToSet': {
                        self._role_permissions(permission_set, component_name, 'namespace'): {
                            '$each': permission_actions
                        }
                    }
                }, permission_set, component_name, created_at)

                updated = yield self.groups.find_one_and_update(component_match_filter, role_update, projection=component_match_filter, return_updated=True, fields=fields).transform(self._extract_component_permission, permission_set, component_name)

                return_value(updated is not None and updated['updatedAt'] == created_at)
            elif permission_type == PermissionType.FullAccess:
                role_update = self._role_permission_update_times({
                    '$set': {
                        self._role_permissions(permission_set, component_name, 'fullAccess'): full_namespace,
                    }
                }, permission_set, component_name, created_at)

                updated = yield self.groups.find_one_and_update(component_match_filter, role_update, projection=component_match_filter, return_updated=True, fields=fields).transform(self._extract_component_permission, permission_set, component_name)

                return_value(updated is not None and updated['updatedAt'] == created_at)
            elif permission_type == PermissionType.NamedScope or permission_type == PermissionType.SpecificEndpoint:
                key = 'scopes' if permission_type == PermissionType.NamedScope else 'endpoints'

                rule_match_filter = deepcopy(component_match_filter)
                rule_match_filter['roles']['$elemMatch']['permissions.{}.{}.{}.{}'.format(permission_set, component_name, key, permission_scope_or_uri)] = {
                    '$exists': True
                }

                rule_new_filter = deepcopy(component_match_filter)
                rule_new_filter['roles']['$elemMatch']['permissions.{}.{}.{}.{}'.format(permission_set, component_name, key, permission_scope_or_uri)] = {
                    '$exists': False
                }

                rule_match = yield self.groups.find_one(rule_match_filter, rule_match_filter)

                if rule_match is None:
                    role_update = self._role_permission_update_times({
                        '$set': {
                            self._role_permissions(permission_set, component_name, key, permission_scope_or_uri): permission_actions,
                        }
                    }, permission_set, component_name, created_at)

                    rule_filter = rule_new_filter
                else:
                    role_update = self._role_permission_update_times({
                        '$addToSet': {
                            self._role_permissions(permission_set, component_name, key, permission_scope_or_uri): {
                                '$each': permission_actions
                            }
                        }
                    }, permission_set, component_name, created_at)

                    rule_filter = rule_match_filter

                updated = yield self.groups.find_one_and_update(rule_filter, role_update, projection=rule_match_filter, return_updated=True, fields=fields).transform(self._extract_component_permission, permission_set, component_name)

                return_value(updated is not None and updated['updatedAt'] == created_at)

    @chainable
    def find_permission_rule(self, group_name, role_name, permission_set, component):
        permission = yield self.groups.find_one({
            'groupName': group_name,
            'roles': {
                '$elemMatch': {
                    'roleName': role_name,
                    'permissions.{}.{}'.format(permission_set, component): {
                        '$exists': True
                    }
                }
            }
        }).transform(self._extract_component_permission, permission_set, component)

        return_value(UserRepository.Groups.Instance.Role.Permissions.ComponentPermission.from_dict(permission) if permission else None)

    @chainable
    def create_client(self, username, client_id, authentication, group_role_permissions):
        created_at = now()

        client_handle = random_uuid()
        user_handle = yield self.find_user(username).handle

        _Client = UserRepository.Clients.Instance

        groups = []
        timestamp_fields = {}

        for group, role_permissions in group_role_permissions.items():
            group_handle = self.find_group(group).handle
            roles = {}

            for role, permissions in role_permissions.items():
                role_handle = self.find_role(group, role).handle

                role_perms = {}
                role_timestamps = ['']

                for uri, actions in permissions.items():
                    g, c, _, e = uri.split('.', 3)

                    # @todo: support subgroups
                    if g == group and self.check_permission(username, g, c, uri, actions, role):
                        role_perms[uri] = _Client.Group.Role.Permission(actions, created_at=created_at)
                        role_timestamps.append(uri)

                roles[role_handle] = role_perms
                timestamp_fields[role_handle] = role_timestamps

            group_perms = _Client.Group(group_handle, roles, created_at=created_at)
            groups.append(group_perms)

        client = _Client(client_handle, user_handle, groups, created_at=created_at)

        created = yield self.clients.find_one_and_update({}, {
            '$setOnInsert': client
        }, upsert=True, return_updated=True, projection={'_id': False}, fields=self._client_permission_timestamps(timestamp_fields))

        return_value(_Client.from_dict(created) if created else None)

    @chainable
    def find_client(self, client_id):
        pass

    @staticmethod
    def _group_permission_timestamps(permission_set, component_name):
        return Fields(timestamp_properties({'roles.permissions': {permission_set: component_name}}))

    @staticmethod
    def _client_permission_timestamps(role_timestamps):
        return Fields(timestamp_properties({'groups.roles': role_timestamps}))

    @staticmethod
    def _group_update_times(update, updated_at):
        if '$set' not in update:
            update['$set'] = {}

        update['$set']['updatedAt'] = updated_at

        return update

    @classmethod
    def _role_update_times(cls, update, updated_at):
        if '$set' not in update:
            update['$set'] = {}

        update['$set']['roles.$.updatedAt'] = updated_at

        return cls._group_update_times(update, updated_at)

    @classmethod
    def _role_permission_update_times(cls, update, permission_set, component, updated_at):
        if '$set' not in update:
            update['$set'] = {}

        update['$set'][cls._role_permissions(permission_set, component, 'updatedAt')] = updated_at

        return cls._role_update_times(update, updated_at)

    @staticmethod
    def _role_permissions(permission_set, *suffixes):
        return 'roles.$.permissions.{}.{}'.format(permission_set, '.'.join(suffixes))

    @staticmethod
    def _extract_group_component(instance):
        if instance is None:
            return instance
        else:
            return instance.get('components', [None])[0]

    @staticmethod
    def _extract_component_permission(instance, permission_set, component_name):
        if instance is None:
            return instance
        else:
            return instance.get('roles', [{}])[0].get('permissions', {}).get(permission_set, {}).get(component_name, None)

    @staticmethod
    def _extract_role(instance):
        if instance is None:
            return instance
        else:
            return instance.get('roles', [None])[0]

    @staticmethod
    def _with_create_time(entry, created_at=None):
        if created_at is None:
            created_at = now()

        entry['createdAt'] = created_at
        entry['updatedAt'] = created_at

        return entry

    @classmethod
    def generate_token(cls, length=30):
        char_count = len(cls._CLIENT_ID_CHARACTER_SET)
        return ''.join(cls._CLIENT_ID_CHARACTER_SET[i % char_count] for i in os.urandom(length))

    @property
    def sessions(self):
        return self.Sessions(self.wrapper)

    @property
    def groups(self):
        return self.Groups(self.wrapper)

    @property
    def clients(self):
        return self.Clients(self.wrapper)
