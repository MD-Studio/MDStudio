from mdstudio.session import GlobalSession


class Event(object):
    # type: CommonSession
    wrapper = None

    def __init__(self, wrapper=None):
        self.wrapper = wrapper or GlobalSession().session

    def push(self, ):
