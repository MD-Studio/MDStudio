from autobahn.twisted.util import sleep as _sleep


def sleep(seconds):
    return _sleep(seconds)
