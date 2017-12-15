from twisted.internet import reactor

def call_later(seconds, callable, *args, **kwargs):
    reactor.callLater(seconds, callable, *args, **kwargs)