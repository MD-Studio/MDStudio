# -*- coding: utf-8 -*-

"""
file: docking.py

Main docking class
"""

from twisted.logger import Logger
logging = Logger()

def init_docking(settings):
    
    logging.info("Init docking component", lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')

def exit_docking(settings):
    
    logging.info("exit docking component", lie_user='mvdijk', lie_session=338776455, lie_namespace='docking')