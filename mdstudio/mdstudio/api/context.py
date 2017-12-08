from copy import deepcopy

from mdstudio.cache.cache_type import CacheType
from mdstudio.db.connection_type import ConnectionType
from mdstudio.logging.log_type import LogType


class IContext(object):
    def __init__(self, session):
        # type: (CommonSession) -> None
        self.session = session  # type: CommonSession

    def get_claims(self, additional_claims):
        if isinstance(additional_claims, dict):
            return deepcopy(additional_claims)
        else:
            return {}

    def get_db_claims(self, connection_type):
        return NotImplementedError('Subclass should implement this')

    def get_log_claims(self, log_type):
        return NotImplementedError('Subclass should implement this')

    def get_cache_claims(self, log_type):
        return NotImplementedError('Subclass should implement this')

    def __enter__(self):
        self.session.call_context_stack.append(self.session.call_context)
        self.session.call_context = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        old_context = self.session.call_context
        self.session.call_context = self.session.call_context_stack.pop()
        assert old_context == self, 'Context switching was done improperly'


class UserContext(IContext):
    def get_db_claims(self, connection_type=ConnectionType.User):
        assert connection_type == ConnectionType.User, 'Only user connections are allowed in the UserContext'

        return self.get_claims({'connectionType': str(connection_type)})

    def get_log_claims(self, log_type=LogType.User):
        assert log_type == LogType.User, 'Only user connections are allowed in the UserContext'

        return self.get_claims({'logType': str(log_type)})

    def get_cache_claims(self, cache_type=CacheType.User):
        assert cache_type == CacheType.User, 'Only user connections are allowed in the UserContext'

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
        assert connection_type in [ConnectionType.User, ConnectionType.Group], 'Only user and group connections are allowed in the GroupContext'

        return self.get_claims({'connectionType': str(connection_type)})

    def get_log_claims(self, log_type=LogType.Group):
        assert log_type in [LogType.User, LogType.Group], 'Only user and group connections are allowed in the GroupContext'

        return self.get_claims({'logType': str(log_type)})

    def get_cache_claims(self, cache_type=CacheType.Group):
        assert cache_type in [CacheType.User, CacheType.Group], 'Only user and group connections are allowed in the GroupContext'

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