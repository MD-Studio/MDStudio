# -*- coding: utf-8 -*-

import logging
import sys

class WorkflowError(Exception):
    
    def __init__(self, message):
        
        super(WorkflowError, self).__init__(message)
        
        logging.error(message)
        