# -*- coding: utf-8 -*-
from lie_logger.log_repository import LogRepository
from mdstudio.api.api_result import APIResult
from mdstudio.api.endpoint import endpoint
from mdstudio.api.exception import CallException
from mdstudio.component.impl.core import CoreComponentSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.logging.log_type import LogType


class LoggerComponent(CoreComponentSession):

    # type: LogRepository
    logs = None

    # type: LoggerComponent.ComponentWaiter
    db_waiter = None
    # type: LoggerComponent.ComponentWaiter
    schema_waiter = None

    @chainable
    def on_run(self):
        yield self.call('mdstudio.auth.endpoint.ring0.set-status', {'status': True})
        yield super(LoggerComponent, self).on_run()

    def pre_init(self):
        self.logs = LogRepository(self.db)
        self.db_waiter = self.ComponentWaiter(self, 'db')
        self.schema_waiter = self.ComponentWaiter(self, 'schema')
        self.component_waiters.append(self.db_waiter)
        self.component_waiters.append(self.schema_waiter)

    @endpoint('mdstudio.logger.endpoint.log', 'log/log-request', 'log/log-response')
    @chainable
    def log_event(self, request, claims=None):
        try:
            res = yield self.logs.insert(claims, request['logs'])
        except CallException as _:
            return_value(APIResult(error='The database is not online, please try again later.'))
        else:
            return_value(len(res))

    def authorize_request(self, uri, claims):
        connection_type = LogType.from_string(claims['logType'])

        # @todo: solve this using jsonschema
        if connection_type == LogType.User:
            return ('username' in claims) == True
        elif connection_type == LogType.Group:
            return ('groups' in claims) == True  # @todo: Properly validate group permissions
        elif connection_type == LogType.GroupRole:
            raise NotImplemented()

        return False
