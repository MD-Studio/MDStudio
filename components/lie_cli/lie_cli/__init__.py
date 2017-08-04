# -*- coding: utf-8 -*-

"""
package:  lie_db

LIEStudio database component
"""

import os

__module__ = 'lie_db'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '15 april 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)

# Import settings
# from .wamp_services import CLIWampApi

# Define component public API
# wampapi  = CLIWampApi

import time

from twisted.internet import reactor
from autobahn import wamp
from queue import Queue, Empty

from lie_corelib.runner import main

from .wamp_services import CLIWampApi

session = CLIWampApi(wamp.ComponentConfig(u'liestudio'))

welcome = """
LIEstudio command line component

This component provides user access via the CLI.
A connected session is available in the "session" variable.

As an example, you can perform calls on a WAMP uri using the following command:
    
    session.call('liestudio.some.uri')
"""

def connect():
    main(session, start_reactor=False)
    return session

def stop():
    session.leave()
    exit()

def block_on(d):
    q = Queue()
    d.addBoth(q.put)

    res = None
    while 1:
        try:
            res = q.get(True, 1)
        except Empty:
            time.sleep(0.1)
        else:
            break

    return res