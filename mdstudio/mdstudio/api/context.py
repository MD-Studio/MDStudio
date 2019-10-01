import mdstudio
import copy
from functools import wraps

import six

from mdstudio.cache.cache_type import CacheType
from mdstudio.db.connection_type import ConnectionType
from mdstudio.logging.log_type import LogType
from mdstudio.util.exception import MDStudioException


class ContextCallable(object):
    def __init__(self, session=None, context=None):
        self._session = session
        self._context = context

    def __call__(self, ctx):
        cc = copy.copy(self)
        cc._context = ctx
        return cc

    @property
    def call_context(self):
        return self._context or (self._session.default_call_context if self._session is not None else None)


class IContext(object):
    def __init__(self, session):
        # type: (CommonSession) -> None
        self.session = session  # type: CommonSession

    def call(self, *args, **kwargs):
        return self.session.call(*args, context=self, **kwargs)

    def get_claims(self, additional_claims):
        if isinstance(additional_claims, dict):
            return copy.deepcopy(additional_claims)
        else:
            return {}

    def get_db_claims(self, connection_type):
        return NotImplementedError('Subclass should implement this')

    def get_log_claims(self, log_type):
        return NotImplementedError('Subclass should implement this')

    def get_cache_claims(self, log_type):
        return NotImplementedError('Subclass should implement this')


class UserContext(IContext):
    def get_db_claims(self, connection_type=mdstudio.db.connection_type.ConnectionType.User):
        from mdstudio.db.connection_type import ConnectionType
        if connection_type != ConnectionType.User:
            raise MDStudioException('Only user connections are allowed in the UserContext')

        return self.get_claims({'connectionType': str(connection_type)})

    def get_log_claims(self, log_type=LogType.User):
        if log_type != LogType.User:
            raise MDStudioException('Only user connections are allowed in the UserContext')

        return self.get_claims({'logType': str(log_type)})

    def get_cache_claims(self, cache_type=CacheType.User):
        if cache_type == CacheType.User:
            raise MDStudioException('Only user connections are allowed in the UserContext')

        return self.get_claims({'cacheType': str(cache_type)})


class GroupContext(UserContext):
    def __init__(self, session, group_name):
        super(GroupContext, self).__init__(session)
        self.group_name = group_name

    def get_claims(self, additional_claims):
        claims = super(GroupContext, self).get_claims(additional_claims)
        claims['asGroup'] = self.group_name
        return claims

    def get_db_claims(self, connection_type=ConnectionType.Group):
        if connection_type not in (ConnectionType.User, ConnectionType.Group):
            raise MDStudioException('Only user and group connections are allowed in the GroupContext')

        return self.get_claims({'connectionType': str(connection_type)})

    def get_log_claims(self, log_type=LogType.Group):
        if log_type not in (LogType.User, LogType.Group):
            raise MDStudioException('Only user and group connections are allowed in the GroupContext')

        return self.get_claims({'logType': str(log_type)})

    def get_cache_claims(self, cache_type=CacheType.Group):
        if cache_type not in (CacheType.User, CacheType.Group):
            raise MDStudioException('Only user and group connections are allowed in the GroupContext')

        return self.get_claims({'cacheType': str(cache_type)})


class GroupRoleContext(GroupContext):
    def __init__(self, session, group_name, role_name):
        super(GroupRoleContext, self).__init__(session, group_name)
        self.role_name = role_name

    def get_claims(self, additional_claims):
        claims = super(GroupRoleContext, self).get_claims(additional_claims)
        claims['asRole'] = self.role_name
        return claims

    def get_db_claims(self, connection_type=ConnectionType.GroupRole):
        return self.get_claims({'connectionType': str(connection_type)})

    def get_log_claims(self, log_type=LogType.GroupRole):
        return self.get_claims({'logType': str(log_type)})

    def get_cache_claims(self, cache_type=CacheType.GroupRole):
        return self.get_claims({'cacheType': str(cache_type)})
