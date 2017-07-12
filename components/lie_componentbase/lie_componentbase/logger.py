import copy

LOGLEVELS = ['debug', 'info', 'warn', 'error', 'critical']


class WampLogger(object):

    def __init__(self, session, log_level='info'):

        self.session = session
        self.log_level = LOGLEVELS.index(log_level)

    def _format_log_message(self, msg, **kwargs):

        if not kwargs:
            logstruct = self.session.session_config.dict()
        else:
            logstruct = copy.deepcopy(kwargs)

        logstruct['log_format'] = msg
        return logstruct

    def debug(self, msg, **kwargs):

        if 0 >= self.log_level:
            message = self._format_log_message(msg, **kwargs)
            message['log_level'] = 'debug'
            self.session.call(u'liestudio.logger.log', message)

    def info(self, msg, **kwargs):

        if 1 >= self.log_level:
            message = self._format_log_message(msg, **kwargs)
            message['log_level'] = 'info'
            self.session.call(u'liestudio.logger.log', message)

    def warn(self, msg, **kwargs):

        if 2 >= self.log_level:
            message = self._format_log_message(msg, **kwargs)
            message['log_level'] = 'warn'
            self.session.call(u'liestudio.logger.log', message)

    def error(self, msg, **kwargs):

        if 3 >= self.log_level:
            message = self._format_log_message(msg, **kwargs)
            message['log_level'] = 'error'
            self.session.call(u'liestudio.logger.log', message)

    def critical(self, msg, **kwargs):

        if 4 >= self.log_level:
            message = self._format_log_message(msg, **kwargs)
            message['log_level'] = 'critical'
            self.session.call(u'liestudio.logger.log', message)
