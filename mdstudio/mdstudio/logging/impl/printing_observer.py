from datetime import datetime

import os

import pytz


class PrintingLogObserver:
    def __init__(self, fp):
        self.fp = fp

    def __call__(self, event):
        if event.get('log_format', None):
            message = event['log_format'].format(**event)
        else:
            message = event.get('message', '')

        pid = str(event.get('pid', os.getpid()))

        log_struct = {
            'time': datetime.fromtimestamp(event['log_time'], pytz.utc).time().replace(microsecond=0).isoformat(),
            'pid': pid,
            'source': event.get('cb_namespace', event['log_namespace']).split('.')[-1],
            'message': message,
            'ws': max(0, 35 - len(pid))
        }

        # log_struct['ws'] = ' ' * max((0, 35 - len(log_struct['source']) - len(log_struct['pid'])))

        self.fp.write('{time} [{source:<{ws}} {pid}]  {message}\n'.format(**log_struct))

