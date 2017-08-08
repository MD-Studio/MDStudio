# -*- coding: utf-8 -*-

"""
IO and subprocess related utility functions.

TODO: Should eventually make there way into the lie_system module
      for general use.
"""

import os
import subprocess
import time
import json

from twisted.logger import Logger

logging = Logger()


def _schema_to_data(schema, data=None, defdict=None):
    
    default_data = defdict or {}
    
    properties = schema.get('properties',{})
    
    for key,value in properties.items():
        if 'default' in value:
            if 'properties' in value:
                default_data[key] = _schema_to_data(value)
            else:
                default_data[key] = value.get('default')
    
    # Update with existing data
    if data:
        default_data.update(data)
    
    return default_data

def prepaire_work_dir(path, user=None, create=False):
    """
    Prepaire a docking working directory at the target path.
    The docking directory is a unique path with a basename composed out of:

        docking-<user name>-<time stamp>

    The function will check the existance of the target path, will try to
    create it if needed and checks if it is writable.
    If any of these checks fail, None will be returned.

    :param path:   target path to prepaire the dockign directory in
    :type path:    str
    :param user:   optional user name to use in the docking path basename
    :type user:    str
    :param create: create the docking directory or return path
    :type create:  bool

    :return:       path name or None in case path could not be created
    :rtype:        str
    """

    # Check if path
    if not path:
        logging.debug('No path defined')
        return None

    # Check if target path exists
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logging.debug('Working directory does not exist. Try creating it: {0}'.format(path))

        # Does not exist, try to create it
        try:
            os.makedirs(path)
        except BaseException:
            logging.error('Unable to create working directory: {0}'.format(path))
            return None

    # Is target directory writable
    if not os.access(path, os.W_OK):
        logging.error('Working directory not writable: {0}'.format(path))
        return None

    # Compose docking directory basename
    dockdir = os.path.join(path, 'docking-{0}-{1}'.format(user or '', int(time.time())))
    while os.path.exists(dockdir):
        dockdir = os.path.join(path, 'docking-{0}-{1}'.format(user or '', int(time.time()) + 5))

    if create:
        try:
            os.makedirs(dockdir)
        except BaseException:
            logging.error('Unable to create working directory: {0}'.format(dockdir))
            return None
    else:
        logging.debug('Create docking working directory path: {0}'.format(dockdir))

    return dockdir

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

PLANTS_DOCKING_SCHEMA = os.path.join(os.path.dirname(__file__), 'plants_docking_schema.json')
settings = _schema_to_data(json.load(open(PLANTS_DOCKING_SCHEMA)))