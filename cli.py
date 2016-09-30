# -*- coding: utf-8 -*-

"""
Command Line Interface to the LIEStudio application
"""

import argparse
import os

def lie_cli(root_path, prog="liestudio"):
  """
  Command Line Interface to the LIEStudio application
  
  :param root_path: path to the application directory
  :type root_path:  str
  :param prog:      CLI program name
  :type prog:       str
  """
  
  # Create the top-level parser
  parser = argparse.ArgumentParser(prog=prog,
                                   description="LIEStudio, binding affinity prediction.")
  
  # Override application configuration file
  parser.add_argument('--config',
                      type=str,
                      default=os.path.join(root_path, 'data/settings.json'),
                      help='Override default application JSON configuration file')
  
  # Set global log level. This may be overridden by the lie_logger component for 
  # individual Twisted Logger observers.
  parser.add_argument('--loglevel',
                      type=str,
                      default='info',
                      choices=['error', 'warn', 'info', 'debug'],
                      help=("Global application log level"))
    
  #parse cmd line args
  options = parser.parse_args()
  
  return options