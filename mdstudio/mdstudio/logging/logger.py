from twisted.internet import reactor
from twisted.logger import Logger as _Logger, LogLevel


class Logger(_Logger):
    pass

def log_critical(event):
    if event.get("log_level") == LogLevel.critical:
        print("Critical error detected, STOPPING reactor:\n", event)
        reactor.stop()