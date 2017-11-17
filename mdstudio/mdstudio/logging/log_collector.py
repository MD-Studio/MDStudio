# coding=utf-8
from datetime import datetime

import pytz
import twisted
from autobahn.wamp.exception import ApplicationError
from twisted.internet import task
from twisted.python.failure import Failure

from mdstudio.api.singleton import Singleton
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.lock import Lock
from mdstudio.deferred.sleep import sleep
from mdstudio.logging.log_type import LogType
from mdstudio.utc import to_utc_string

LOGLEVELS = ['debug', 'info', 'warn', 'error', 'critical']


class SessionLogCollector(metaclass=Singleton):
    def __init__(self, session, log_type=LogType.User):
        self.session = session
        self.log_type = log_type
        self.logs = []
        self.lock = Lock()
        self.flusher_lock = Lock()
        self.flushing = False

        session.log.info('Collectiong logs on session {session}', session=session)

        twisted.python.log.addObserver(self)

        self.flusher = task.LoopingCall(self.flush_logs)

    def __call__(self, event):
        if event.get('log_format', None):
            message = event['log_format'].format(**event)
        else:
            message = event.get('message', '')

        self.append_log({
            'level': event['log_level'].name,
            'source': event['log_namespace'],
            'time': to_utc_string(datetime.fromtimestamp(event['log_time'], tz=pytz.utc)),
            'message': message
        })

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
            except ApplicationError:
                yield self.lock.release()
                # The log component is probably not awake yet, wait a bit longer
                yield sleep(1)
            except Exception as e:
                yield self.lock.release()
                print(e)
            else:
                yield self.lock.release()

        if count < 10:
            yield sleep(1)

    @chainable
    def start_flushing(self):
        yield self.flusher_lock.acquire()
        if not self.flushing:
            self.flusher.start(1)
            self.flushing = True

        yield self.flusher_lock.release()

    @chainable
    def pause_flushing(self):
        yield self.flusher_lock.acquire()
        if self.flushing:
            self.flusher.stop()
            self.flushing = False

        yield self.flusher_lock.release()
