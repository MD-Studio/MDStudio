# -*- coding: utf-8 -*-

"""
IO and subprocess related utility functions.

TODO: Should eventually make there way into the lie_system module
      for general use.
"""

import os
import subprocess

from   twisted.logger import Logger

logging = Logger()

def prepaire_work_dir(path):
    
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logging.debug('Working directory does not exist. Try creating it: {0}'.format(path))
        
        try:
            os.makedirs(path)
        except:
            logging.error('Unable to create working directory: {0}'.format(path))
            return False
    
    return True

def cmd_runner(cmd, workdir):
    
    # Get current directory
    currdir = os.getcwd()
    
    # Change to workdir
    os.chdir(workdir)
    
    # Run cli command
    logging.debug('Execute cli process: {0}'.format(' '.join(cmd)))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = process.communicate()
    if process.returncode != 0:
        logging.warn('Executable stopped with non-zero exit code ({0}). Error: {1}'.format(process.returncode, errors))
    
    # Change back to currdir
    os.chdir(currdir)
    
    return output, errors