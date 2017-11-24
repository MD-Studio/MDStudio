# coding=utf-8
import json
from datetime import datetime

import os
import pytz
import six
import twisted
from autobahn.twisted import ApplicationSession
from autobahn.wamp.exception import ApplicationError, TransportLost
from twisted.internet import task, reactor
from twisted.python.failure import Failure

from mdstudio.api.call_exception import CallException
from mdstudio.api.singleton import Singleton
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock
from mdstudio.deferred.sleep import sleep
from mdstudio.logging.log_type import LogType
from mdstudio.logging.logger import Logger
from mdstudio.utc import to_utc_string

LOGLEVELS = ['debug', 'info', 'warn', 'error', 'critical']

@six.add_metaclass(Singleton)
class SessionLogObserver(object):
    log = Logger()

    def __init__(self, session, log_type=LogType.User):
        self.session = None
        self.sessions = []
        self.log_type = log_type
        self.logs = []
        self.lock = Lock()
        self.flusher_lock = Lock()
        self.flushing = False

        self.recovery_file_path = os.path.join(session.component_root_path(), 'logs', 'recovery.json')

        twisted.python.log.addObserver(self)
        self.log.info('Collecting logs on session {session}', session=session)

        self.flusher = task.LoopingCall(self.flush_logs)

        reactor.addSystemEventTrigger('before', 'shutdown', self.store_recovery)

    def __call__(self, event):
        if event.get('log_format', None):
            message = event['log_format'].format(**event)
        else:
            message = event.get('message', '')

        if message:
            self.append_log({
                'level': event['log_level'].name,
                'source': event['log_namespace'],
                'time': to_utc_string(datetime.fromtimestamp(event['log_time'], tz=pytz.utc)),
                'message': message
            })
        # else:
        #     raise NotImplementedError('No message')

    @chainable
    def store_recovery(self):
        yield self.lock.acquire()
        if len(self.logs) > 0:
            with open(self.recovery_file_path, 'w') as recovery_file:
                json.dump(self.logs, recovery_file)
                self.logs = []
        yield self.lock.release()

    @chainable
    def append_log(self, log):
        yield self.lock.acquire()
        self.logs.append(log)
        yield self.lock.release()

    @chainable
    def flush_logs(self):
        yield self.lock.acquire()
        count = len(self.logs)

        if count > 0:
            try:
                yield self.session.flush_logs(self.logs)
                self.logs = []
            except TimeoutError:
                yield self.lock.release()
                # The crossbar router is down, wait a few seconds to see if it is back up
                yield sleep(3)
            except (ApplicationError, TransportLost, CallException):
                yield self.lock.release()
                # The log or db component is probably not awake yet, wait a bit longer
                yield sleep(1)
            except Exception as e:
                yield self.lock.release()
                self.log.error('Unrecognized exception during logging {failure}', failure=e)
            except:
                yield self.lock.release()
            else:
                yield self.lock.release()
        else:
            yield self.lock.release()

        if count < 10:
            yield sleep(1)

    @chainable
    def start_flushing(self, session):
        yield self.lock.acquire()

        recovery = self.recovery_file(session)

        if os.path.isfile(recovery):
            try:
                with open(recovery, 'r') as recovery_file:
                    self.logs = json.load(recovery_file)
            except:
                pass
            finally:
                os.remove(recovery)

        yield self.lock.release()

        yield self.flusher_lock.acquire()

        if not self.flushing:
            self.session = session
            self.flusher.start(1)
            self.flushing = True
        else:
            self.sessions.append(session)

        yield self.flusher_lock.release()

    @chainable
    def pause_flushing(self, session):
        yield self.flusher_lock.acquire()

        if self.flushing:
            if self.session == session:
                self.session = None

                for s in self.sessions:
                    if s.is_connected:
                        self.sessions.remove(s)
                        self.session = s
                        break
            else:
                self.sessions.remove(session)

            if not self.session:
                self.flusher.stop()
                self.flushing = False

        yield self.flusher_lock.release()

    @staticmethod
    def recovery_file(session):
        return os.path.join(session.component_root_path(), 'logs', 'recovery.json')