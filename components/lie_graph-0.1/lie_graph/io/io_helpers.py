# -*- coding: utf-8 -*-

import sys
import os
import collections
import json
import StringIO
import logging

from   .. import __version__

def _check_lie_graph_version(version=None):
    """
    Check if the graph version of the file is (backwards) compatible with
    the current lie_graph module vesion
    """
    
    try:
        version = float(version)
    except:
        logging.error('No valid lie_graph version identifier {0}'.format(version))
        return False
    
    if version > float(__version__):
        logging.error('Graph made with a newer version of lie_graph {0}, you have {1}'.format(version, __version__))
        return False
        
    return True    
    
def _open_anything(source, mode='r'):
    """
    Open input available from a file, a Python file like object, standard
    input, a URL or a string and return a uniform Python file like object
    with standard methods.
    
    :param source: Input as file, Python file like object, standard
                   input, URL or a string
    :type source:  mixed
    :param mode:   file access mode, defaults to 'r'
    :type mode:    string
    :return:       Python file like object
    """
    
    # Check if the source is a file and open
    if os.path.isfile(source):
        logging.debug('Reading file from disk {0}'.format(source))
        return open(source, mode)
    
    # Check if source is file already openend using 'open' or 'file' return
    if hasattr(source, 'read'):
        logging.debug('Reading file {0} from file object'.format(source.name))
        return source
    
    # Check if source is standard input
    if source == '-':
        logging.debug('Reading file from standard input')
        return sys.stdin
    
    else:
        # Check if source is a URL and try to open
        try:
    
            import urllib2, urlparse
            if urlparse.urlparse(source)[0] == 'http':
                result = urllib.urlopen(source)
                loggin.debug("Reading file from URL with access info:\n {0}".format(result.info()))
                return result
        except:
            logging.info("Unable to access URL")    
    
        # Check if source is file and try to open else regard as string
        try:
            return open(source)
        except:
            logging.debug("Unable to access as file, try to parse as string")
            return StringIO.StringIO(str(source))

def _flatten_nested_dict(config, parent_key='', sep='.'):
    """
    Flatten a nested dictionary by concatenating all 
    nested keys. 
    Keys are converted to a string representation if
    needed.
    
    :param config:     dictionary to flatten
    :type config:      dict
    :param parent_key: leading string in concatenated keys
    :type parent_key:  str
    :param sep:        concatenation seperator
    :type sep:         str
    :return:           flattened dictionary
    :rtype:            dict
    """
    
    items = []
    for key,value in config.items():
      
        # parse key to string if needed
        if type(key) not in (str,unicode):
            logging.debug('Dictionary key {0} of type {1}. Parse to unicode'.format(key, type(key)))
            key = unicode(key)
      
        new_key = unicode(parent_key + sep + key if parent_key else key)
        if isinstance(value, collections.MutableMapping):
            items.extend(_flatten_nested_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)

def _nest_flattened_dict(graph_dict, sep='.'):
    """
    Convert a dictionary that has been flattened by the
    `_flatten_nested_dict` method to a nested representation

    :param graph_dict: dictionary to nest
    :type graph_dict:  dict
    :param sep:        concatenation seperator
    :type sep:         str
    
    :return:           nested dictionary
    :rtype:            dict
    """
  
    nested_dict = {}
    for key,value in sorted(graph_dict.items()):
    
        splitted = key.split(sep)
        if len(splitted) == 1:
            nested_dict[key] = value
    
        d = nested_dict
        for k in splitted[:-1]:
            if not k in d:
                d[k] = {}
            d = d[k]
    
        d[splitted[-1]] = value
    
    return nested_dict
