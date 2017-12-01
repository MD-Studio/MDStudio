from autobahn.wamp import auth

from mdstudio.api.exception import CallException
from mdstudio.component.impl.common import CommonSession
from mdstudio.db.connection import ConnectionType
from mdstudio.db.session_database import SessionDatabaseWrapper
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.deferred.sleep import sleep
from mdstudio.logging.log_type import LogType
from mdstudio.logging.logger import Logger


class CoreComponentSession(CommonSession):
    class ComponentWaiter(object):
        log = Logger()

        def __init__(self, session, component):
            # type: (CoreComponentSession, str) -> None
            self.session = session
            self.component = component

        @chainable
        def wait(self):
            online = False
            tried = False

            def status_call():
                return self.session.call('mdstudio.auth.endpoint.ring0.get-status', {'component': self.component})

            try:
                online = yield status_call()
            except:
                self.log.info('{waiter} is waiting for {waitee}', waiter=self.session.class_name(), waitee=self.component)
                tried = True

            while not online:
                try:
                    online = yield status_call()
                except CallException:
                    yield sleep(0.1)
                except Exception as e:
                    self.log.error('Component {component} not online, and caught '
                                   'unrecognized exception {exc}.', component=self.component, exc=e)
                    yield sleep(1)
                else:
                    yield sleep(0.1)

            if tried:
                self.log.info('{waitee} is now online, continuing '
                              'execution for {waiter}', waitee=self.component, waiter=self.session.class_name())

    def __init__(self, config=None):
        self.component_waiters = []
        self.db = SessionDatabaseWrapper(self, ConnectionType.User)
        super(CoreComponentSession, self).__init__(config)

    def pre_init(self):
        self.log_type = LogType.Group
        self.component_config.session['context'] = {
            'group': 'mdstudio',
            'role': self.component_config.static.component
        }

    def on_connect(self):
        auth_methods = [u'ticket']
        authid = self.component_config.session.username
        auth_role = authid

        self.join(self.config.realm, authmethods=auth_methods, authid=authid, authrole=auth_role)

    onConnect = on_connect

    @chainable
    def on_run(self):
        yield self.ComponentWaiter(self, 'logger').wait()

    @chainable
    def _on_join(self):
        print('{} is waiting for {}'.format(self.class_name(), [waiter.component for waiter in self.component_waiters]))

        for waiter in self.component_waiters:
            yield waiter.wait()

        yield super(CoreComponentSession, self)._on_join()

    def on_challenge(self, challenge):
        if challenge.method == u'ticket':
            return self.component_config.session.username
        else:
            raise Exception("Core components should only use ticket for authentication for development, attempted to use {}".format(challenge.method))

    onChallenge = on_challenge

    def load_settings(self):
        self.component_config.session['username'] = u'{}'.format(self.class_name().lower().replace('component', '', 1))
        self.component_config.static['vendor'] = u'mdstudio'
        self.component_config.static['component'] = u'{}'.format(self.component_config.session.username)

        super(CoreComponentSession, self).load_settings()

    @chainable
    def flush_logs(self, logs):
        with self.group_context('mdstudio'):
            result = yield self.call(u'mdstudio.logger.endpoint.log', {'logs': logs}, claims={'logType': str(LogType.Group)})

        return_value(result)
