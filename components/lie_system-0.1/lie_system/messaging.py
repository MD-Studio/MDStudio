# -*- coding: utf-8 -*-

"""
file: wamp_message_format.py
"""

class WampMessageFormat(object):
  
  def __init__(self):
    
    self.message = {
      'result': None,
      'log': None,
      'log_code': None,
      'status': True
    }