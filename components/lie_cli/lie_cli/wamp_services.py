import time
import re
import os

from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn.wamp import SubscribeOptions, PublishOptions
from autobahn import wamp

from lie_corelib import BaseApplicationSession, register, WampSchema
from lie_corelib.config import config_from_dotenv, config_to_dotenv

try:
    input = raw_input
except NameError:
    pass

class CLIWampApi(BaseApplicationSession):
    def preInit(self, **kwargs):
        has_credentials = True
        conf_file = os.path.join(self._config_dir, '.env')
        if os.path.isfile(conf_file):
            env = config_from_dotenv(conf_file)
            if not ('authid' in env or self.session_config_environment_variables.get('authid') in env):
                has_credentials = False
            if not ('password' in env or self.session_config_environment_variables.get('password') in env):
                has_credentials = False
        else:
            has_credentials = False

        if not has_credentials:
            print("Go to ... and create a client with proper scope permissions.")
            print("Then input the credentials here")
            conf = {}
            conf[self.session_config_environment_variables.get('authid', 'authid')] = input('Cient ID: ')
            conf[self.session_config_environment_variables.get('password', 'password')] = client_secret = input('Cient Secret: ')

            config_to_dotenv(conf, conf_file)
            print('Config is now written to {}'.format(conf_file))
            exit()