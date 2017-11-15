# coding=utf-8
import json
from datetime import datetime
from json import JSONDecodeError

import os
import pytz
from autobahn.twisted.util import sleep
from autobahn.wamp.exception import ApplicationError
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.python.failure import Failure

from mdstudio import is_python3

if is_python3:
    # noinspection PyCompatibility
    from queue import Queue, Empty
else:
    # noinspection PyCompatibility
    from Queue import Queue, Empty


def block_on(d, timeout=None):
    q = Queue()
    d.addBoth(q.put)
    try:
        ret = q.get(timeout is not None, timeout)
    except Empty:
        raise TimeoutError
    if isinstance(ret, Failure):
        ret.raiseException()
    else:
        return ret


LOGLEVELS = ['debug', 'info', 'warn', 'error', 'critical']


class PrintingObserver:
    """
    ILogObserver that writes formatted log events to stdout or stderr

    :param out:          Output stream as sys.stdout or sys.stderr
    :type out:           File object representing Python interpreter standard
                         output or error stream
    :param format_event: Format string suitable for parsing using the Formatter
                         class (Python format buildin). The log event dictionary
                         is passed to the format function.
    :type format_event:  String with optional format replacement fields
    :param datefmt:      Date and time format string following strftime convention
    :type datefmt:       string
    """

    def __init__(self, out, namespace=None, min_level='info', **kwargs):
        self._out = open(out, 'w') if out == os.devnull else out

        self.format_event = '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n'
        self.namespace = namespace
        self.min_level_index = LOGLEVELS.index(min_level)

    def __call__(self, event):
        """
        Evaluate event dictionary, format the log message and
        write to output stream

        :param event: Twisted logger event
        :type event : dict
        """
        if self.namespace and not event['log_namespace'] == self.namespace:
            return

        level = event.get("log_level", None)
        if level is None:
            levelName = u"-"
        else:
            levelName = level.name

        if LOGLEVELS.index(levelName) >= self.min_level_index:
            if event.get('log_format', None):
                message = event['log_format'].format(**event)
            else:
                message = event.get('message', '')

            oldMsg = event.pop('message')

            asctime = datetime.fromtimestamp(event['log_time'], tz=pytz.utc).isoformat()
            self._out.write(self.format_event.format(asctime=asctime, message=message, **event))

            if oldMsg:
                event['message'] = oldMsg


class WampLogObserver(object):
    def __init__(self, session, file, min_level='info'):
        self.format_event = '{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n'

        self.session = session
        self.namespace = self.session.component_info.get('namespace')
        self.logger_namespace = self.session.session_config['loggernamespace']
        self.min_level_index = LOGLEVELS.index(min_level)
        self.log_list = []
        self.log_queue = Queue()
        self.shutdown = False

        if file:
            try:
                self.log_list = json.load(file)
            except JSONDecodeError:
                pass

    def __call__(self, event):
        if self.namespace and not event['log_namespace'] == self.namespace:
            return

        level = event.get("log_level", None)
        if level is None:
            levelName = u"-"
        else:
            levelName = level.name

        if LOGLEVELS.index(levelName) >= self.min_level_index:
            if event.get('log_format', None):
                message = event['log_format'].format(**event)
            else:
                message = event.get('message', '')

            logstruct = {
                'level': levelName,
                'namespace': self.session.component_info['namespace'],
                'user': self.session.session_config.get('authid', self.session.session_config.get('role')),
                'time': datetime.fromtimestamp(event['log_time'], tz=pytz.utc),
                'message': message
            }

            self.log_queue.put(logstruct)

    def start_flushing(self):
        self.session.log.info('Started flushing logs for {package}', package=self.session.component_info['package_name'])
        reactor.callLater(0.1, self._flush)

    def stop_flushing(self):
        self.shutdown = True

    @inlineCallbacks
    def _flush(self):
        while not self.log_queue.empty() and not self.shutdown:
            try:
                rlog = self.log_queue.get(timeout=0.1)
            except TimeoutError as e:
                pass
            else:
                self.log_list.append(rlog)

        if len(self.log_list) > 0 and not self.shutdown:
            try:
                yield self.session.flush_logs(self.logger_namespace, self.log_list)
            except ApplicationError as e:
                print(e)
                yield sleep(5)
            else:
                self.log_list = []

        if not self.shutdown:
            # enqueue again
            reactor.callLater(5, self._flush)

    def flush_remaining(self, file):
        while not self.log_queue.empty():
            self.log_list.append(self.log_queue.get())

        json.dump(self.log_list, file)
        file.flush()
