# -*- coding: utf-8 -*-

import os
import stat
import logging

from twisted.logger import Logger
from executor import ExternalCommand

logging = Logger()

class CLIRunner(object):
    
    def __init__(self, **kwargs):
        
        self._executor_commands = kwargs
    
    def _check_executable(self, exe_path):
        
        if not os.path.exists(exe_path):
            logging.error('{0} executable does not exist at: {1}'.format(exe, exe_path))
            return False
    
        if not os.access(exe_path, os.X_OK):
            
            try:
                st = os.stat(exe_path)
                os.chmod(exe_path, st.st_mode | stat.S_IEXEC)
            except:
                logging.error('{0} not executable'.format(exe_path))
                return False
    
        return True
    
    def run(self, cmd):
        
        # Check if executable is available (first argument)
        if not self._check_executable(cmd[0]):
            return
        
        runner = ExternalCommand(' '.join(cmd), capture=True, check=False, **self._executor_commands)
        output = runner.start()
        
        return runner