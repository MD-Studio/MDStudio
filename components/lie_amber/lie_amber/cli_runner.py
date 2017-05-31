# -*- coding: utf-8 -*-

import os
import logging

from   executor import ExternalCommand
 
class CLIRunner(object):
    
    def __init__(self, **kwargs):
        
        self._executor_commands = kwargs
    
    def _check_executable(self, exe_path):
        
        if not os.path.exists(exe_path):
            logger.error('{0} executable does not exist at: {1}'.format(exe, exe_path))
            return False
    
        if not os.access(exe_path, os.X_OK):
            logger.error('{0} not executable'.format(exe_path))
            return False
    
        return True
    
    def run(self, cmd):
        
        # Check if executable is available (first argument)
        if not self._check_executable(cmd[0]):
            return
        
        runner = ExternalCommand(' '.join(cmd), capture=True, **self._executor_commands)
        output = runner.start()
        
        return runner