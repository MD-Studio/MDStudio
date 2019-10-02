# -*- coding: utf-8 -*-
from logger.log_repository import LogRepository
from mdstudio.api.api_result import APIResult
from mdstudio.api.comparison import Comparison
from mdstudio.api.endpoint import endpoint, cursor_endpoint
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
        self.logs = LogRepository(self.db)(self.grouprole_context('mdstudio', 'logger'))
        self.db_waiter = self.ComponentWaiter(self, 'db', self.group_context('mdstudio'))
        self.schema_waiter = self.ComponentWaiter(self, 'schema', self.group_context('mdstudio'))
        self.component_waiters.append(self.db_waiter)
        self.component_waiters.append(self.schema_waiter)

        super(LoggerComponent, self).pre_init()

    @cursor_endpoint('mdstudio.logger.endpoint.get-logs', 'get/logs-request/v1', 'get/logs-response/v1')
    def get_logs(self, request, claims, **kwargs):

        with self.grouprole_context('mdstudio', 'logger'):

            logfilter = {}
            if 'level' in request:
                logfilter['level'] = {
                    '${}'.format(Comparison.from_string(logfilter['level']['comparison'])): self._map_level(logfilter['level']['value'])
                }
            if 'source' in request:
                logfilter['source'] = {'$regex': logfilter['source']['pattern']}
                if 'options' in request['source']:
                    logfilter['source']['$options'] = request['source']['options']
            if 'time' in request:
                logfilter['time'] = {}
                if 'since' in request['time']:
                    logfilter['time']['$gte'] = request['time']['since']
                if 'until' in request['time']:
                    logfilter['time']['$lte'] = request['time']['until']
            if 'createdAt' in request:
                logfilter['createdAt'] = {}
                if 'since' in request['createdAt']:
                    logfilter['createdAt']['$gte'] = request['createdAt']['since']
                if 'until' in request['createdAt']:
                    logfilter['createdAt']['$lte'] = request['createdAt']['until']

            return self.logs.get(logfilter, claims, **kwargs)

    @endpoint('push-logs', 'push/logs-request/v1', 'push/logs-response/v1')
    @chainable
    def push_logs(self, request, claims=None):
        try:
            res = yield self.logs.insert(self._clean_claims(claims), [self._map_level(l) for l in request['logs']])
        except CallException as _:
            return_value(APIResult(error='The database is not online, please try again later.'))
        else:
            return_value({
                'inserted': len(res)
            })

    @endpoint('push-event', 'push/event-request/v1', 'push/event-response/v1')
    @chainable
    def push_event(self, request, claims=None):
        try:
            event = request['event']
            tags = event.pop('tags')
            res = yield self.logs.insert(self._clean_claims(claims), [self._map_level(event)], tags)
        except CallException as _:
            return_value(APIResult(error='The database is not online, please try again later.'))
        else:
            return_value(len(res))

    def authorize_request(self, uri, claims):
        connection_type = LogType.from_string(claims['logType'])

        if connection_type == LogType.User:
            return ('username' in claims) is True
        elif connection_type == LogType.Group:
            return ('group' in claims) is True
        elif connection_type == LogType.GroupRole:
            return all(key in claims for key in ['group', 'role'])

        return False

    @staticmethod
    def _map_level(log, from_int=False):
        from_map = {
            'debug': 0,
            'info': 10,
            'warn': 20,
            'error': 30,
            'critical': 40
        }
        to_map = {
            0: 'debug',
            10: 'info',
            20: 'warn',
            30: 'error',
            40: 'critical'
        }
        if from_int:
            log['level'] = to_map[log['level']]
        else:
            log['level'] = from_map[log['level']]
        return log

    @staticmethod
    def _clean_claims(claims):

        return claims
