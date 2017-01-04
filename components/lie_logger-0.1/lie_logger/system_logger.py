# -*- coding: utf-8 -*-

"""
Twisted Logging logger classes
"""

__all__ = ['init_application_logging',
           'exit_application_logging',
           'customFilterPredicate',
           'PrintingObserver',
           'RotateFileLogObserver',
           'ExportToMongodbObserver']

import sys
import os
import time
import copy
import io

from   datetime import datetime
from   pymongo import MongoClient
from   zope.interface import provider, implementer
from   twisted.logger import (ILogObserver, ILogFilterPredicate, PredicateResult, LogLevel,
                              globalLogPublisher, Logger, FilteringLogObserver, LogLevelFilterPredicate)

from   lie_logger.log_serializer import LogSerializer

logging = Logger()

# Make an instance of the log serializer for log storage in MongoDB
log_serializer = LogSerializer(max_depth=2)

# Connect to MongoDB.
# TODO: this should be handled more elegantly
db = None#MongoClient(host='localhost', port=27017)['liestudio']


class InvalidObserverError(Exception):
    """
    InvalidObserverError Exception
    
    Someone tried to register an invalid observer to the logging system.
    """

    def __init__(self, observer):
        """
        @param observer: an observer
        """

        super(InvalidObserverError, self).__init__(str(observer))


def init_application_logging(settings, config):
    """
    Logging component bootstrap routines
    
    Add Twister log message observers to the globalLogPublisher
    based on predefined logger module settings.
    
    :param settings: global and module specific settings
    :type settings:  dict or dict like object
    :return:         true/false for successful bootstrap completion
    :rtype:          bool
    """

    # @todo: again this should be fixed in a nicer way
    global db
    if db is None:
        db = MongoClient(host=config.get('lie_db.host'), port=config.get('lie_db.port'))['liestudio']

    current_module = sys.modules[__name__]
    observers = settings['observers']
    for observer in observers:
        if observers[observer].get('activate', False):
            if hasattr(current_module, observer):

                # Add log filter predicates
                filter_predicates = []
                for predicate_name, predicate_function in observers[observer].get('filter_predicate', {}).items():

                    # For log_level settings use Twisted LogLevelFilterPredicate observer
                    if predicate_name == 'log_level':
                        filter_predicates.append(
                            LogLevelFilterPredicate(defaultLogLevel=LogLevel.levelWithName(predicate_function)))

                    # For all other event arguments (predicate_name) use customFilterPredicate observer
                    else:
                        filter_predicates.append(customFilterPredicate(
                            predicate_name,
                            _compile_filter_predicates(predicate_function)
                        ))

                obs_object = getattr(current_module, observer)
                if len(filter_predicates):
                    init_observer = FilteringLogObserver(observer=obs_object(**observers[observer]),
                                                         predicates=filter_predicates)
                else:
                    init_observer = obs_object(**observers[observer])

                # Same observer can be added multiple times with different settings
                globalLogPublisher.addObserver(init_observer)
                logging.debug('Init {0} logging observer'.format(observer))
            else:
                raise InvalidObserverError(observer)

    # Check for MongoDB database
    # TODO: should make a wrapper around PyMongo connection for easy checking connection
    if not db:
        logging.error('Unable to connect to database')
        return False

    # Check if the database has a 'log' collection
    if 'log' not in db.collection_names():
        logging.info('Creating database "log" collection')
    log_collection = db['log']

    return True


def exit_application_logging(settings):
    """
    Logging component exit routines
    
    Flush the log buffer of the ExportToMongodbObserver observer
    to the database.
    
    :param settings: global and module specific settings
    :type settings:  dict or dict like object
    :return:         true/false for successful bootstrap completion
    :rtype:          bool
    """
    # Flush log messages to database before shutdown
    for observer in globalLogPublisher._observers:
        if type(observer).__name__ in ('ExportToMongodbObserver', 'RotateFileLogObserver'):
            observer.flush()

    return True


def _compile_filter_predicates(predicate):
    """
    Compile custom filter predicates for evaluation in the
    customFilterPredicate observer
    
    Allowed predicate evaluation functions:
    - '<operator> <predicate value>' where operator equals 
      ==, != or <> will evaluate equality between two values
      parsed as string. For booleans this means False == False
      but False != 0.
    - '<operator> <predicate value>' where operator equals
      <, >, <=, >= will evaluate equality between two numeric
      values.
    
    :param predicate: predicate function
    :type predicate:  string
    :return:          compiled predicate evaluation function
    :rtype:           object
    """
    splitted = predicate.split()
    operator = splitted[0]
    test_val = ' '.join(splitted[1:])
    if operator in ('==', '!=', '<>'):
        return compile('str(_pred_test) {0} "{1}"'.format(operator, test_val), 'logger', 'eval')
    elif operator in ('>', '<', '<=', '>='):
        return compile('_pred_test {0} float({1})'.format(operator, test_val), 'logger', 'eval')
    else:
        raise Exception("Operator not allowed: {0}".format(splitted[0]))


def _format_logger_event(event, datefmt=None):
    """
    Check Twisted logger event and add missing attributes
    """
    # Twisted event instances are shared among observers. 
    # Only need to format once. Check by looking for 'asctime' parameter
    if not 'asctime' in event:
        if datefmt:
            event['asctime'] = datetime.fromtimestamp(event['log_time']).strftime(datefmt)

        if event.get('log_format', None):
            event['message'] = event['log_format'].format(**event)
        else:
            event['message'] = ''

    return event


def _serialize_logger_event(event, discard=['log_source', 'log_logger']):
    """
    Serialize event dictionary for storage in MongoDB.
    
    Checks all the key/value pairs in the Twisted logger event dictionary
    and:
    - discard keys in discard list
    - store log_level name from object 
    - serialize dictionary using LogSerializer, discard all nested elements
      below depth level 2.
    
    :param discard: event keys discarded in the serialized event dict 
    :type discard:  list
    :return:        copy of event dict suitable for PyMongo BSON serialization
    :rtype:         dict
    """
    
    event = _format_logger_event(event)

    new_event = {}
    for key, value in event.items():

        # Do not store fields in discard list
        if key in discard:
            continue

        # Store log_level name string of LogLevel object    
        if key == 'log_level':
            new_event['log_level'] = value.name

        # Store log_time as int
        elif key == 'log_time':
            new_event[key] = int(value)
        else:
            new_event[key] = value

    return log_serializer.encode(new_event)


@implementer(ILogFilterPredicate)
class customFilterPredicate(object):
    """
    ILogFilterPredicate that evaluates events against a series of
    custom filter predicates compiled using the _compile_filter_predicates
    method.
    
    :param predicate_name:     the event argument to evaluate
    :type predicate_name:      string
    :param predicate_function: compiled evaluation function for the 
                               predicate from _compile_filter_predicates
    :type predicate_function:  object
    """

    def __init__(self, predicate_name, predicate_function):

        self._predicate_name = predicate_name
        self._predicate_function = predicate_function

    def __call__(self, event):
        """
        Evaluates the compiled filter predicate for a given event 
        argument.
        
        If the event argument is not defined a PredicateResult.maybe
        is returned.
        """
        _pred_test = event.get(self._predicate_name, None)

        if _pred_test:

            # TODO: Evaluation is performed using 'eval' with stripped environment
            # on a pre-parsed and compiled function but still eval is not safe
            if eval(self._predicate_function, {'__builtins__': {}}, {}):
                return PredicateResult.yes
            return PredicateResult.no

        return PredicateResult.maybe


@provider(ILogObserver)
class PrintingObserver(object):
    """
    ILogObserver that writes formatted log events to stdout or stderr
    
    :param out:          Output stream as sys.stdout or sys.stderr
    :type out:           File object representing Python interpreter standard 
                         output or error stream
    :param format_event: Format string suitable for parsing using the Formatter 
                         class (Python format buildin). The log event dictionary
                         is passed to the format function.
    :type format_event:  String with optional format replacement fields  
    :param datefmt:      Date and time format string following strftime convention
    :type datefmt:       string
    """

    def __init__(self, out='stdout', format_event='{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n',
                 datefmt='%Y-%m-%d %H:%M:%S', **kwargs):
        self._out = sys.stdout
        if out == 'stderr':
            self._out = sys.stderr

        self._format_event = format_event
        self._datefmt = datefmt

    def __call__(self, event):
        """
        Evaluate event dictionary, format the log message and
        write to output stream
        
        :param event: Twisted logger event
        :type event : dict
        """
        event = _format_logger_event(event, datefmt=self._datefmt)
        self._out.write(self._format_event.format(**event))


@provider(ILogObserver)
class RotateFileLogObserver(object):
    """
    ILogObserver that writes formatted log events to a logfile and
    rotates the logfile after a set time.
    
    :param out_file:      File to write log messages to
    :type out_file:       Absolute path as string
    :param format_event:  Format string suitable for parsing using the Formatter 
                          class (Python format buildin). The log event dictionary
                          is passed to the format function.
    :type format_event:   String with optional format replacement fields  
    :param datefmt:       Date and time format string following strftime convention
    :type datefmt:        string
    :param rotation_time: Log rotation time in seconds
    :type rotation_time:  int
    """

    def __init__(self, logfile_path, format_event='{asctime} - [{log_level.name:<5}: {log_namespace}] - {message}\n',
                 datefmt='%Y-%m-%d %H:%M:%S', rotation_time=86400, encoding='utf8', **kwargs):

        self._logfile_path = os.path.abspath(logfile_path)
        self._logfile_dir = os.path.dirname(self._logfile_path)
        self._logfile_name = os.path.basename(self._logfile_path)
        self._logfile_encoding = encoding

        if not os.path.exists(self._logfile_dir):
            raise IOError('Directory for writting log files to does not exist: {0}'.format(self._logfile_dir))

        self._format_event = format_event
        self._datefmt = datefmt
        self._rotation_time = rotation_time

        self._create_logfile()

    def __call__(self, event):
        """
        Evaluate event dictionary, format the log message and
        write to logfile.
        Check if the file rotation time has been passed and rotate
        the logfile if so.
        
        :param event: Twisted logger event
        :type event:  dict
        """
        if time.time() >= self._logfile_ctime + self._rotation_time:
            self._rotate_logfile()

        event = _format_logger_event(event, datefmt=self._datefmt)
        self._logfile.write(self._format_event.format(**event))

    def _get_logfile_ctime(self):
        """
        Unix based systems do often not store the file creation timestamp as
        part of the file metadata. We store it in the first line of the log
        file.
        """
        # Try get file creation timestamp from first line of log file
        self._logfile.seek(0)
        try:
            self._logfile_ctime = int(self._logfile.readline().strip())
        except:
            logging.warn("unable to read logfile creation stamp from first line")
            self._logfile_ctime = int(time.time())

    def _rotate_logfile(self):
        """
        Close the current active logfile, back it up by adding a datestamp
        to the filename and create a new logfile.
        """
        if os.path.isfile(self._logfile_path):
            basename, extention = os.path.splitext(self._logfile_name)
            timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
            backup_filename = '{0}/{1}_{2}{3}'.format(self._logfile_dir, basename, timestamp, extention)
            logging.debug('Rotate logfile after {0} sec. to: {1}'.format(self._rotation_time, backup_filename))

            self._logfile.flush()
            self._logfile.close()
            os.rename(self._logfile_path, backup_filename)

            self._create_logfile()

    def _create_logfile(self):
        """
        Create a new logfile.
        Store the file creation time stamp in the first line of the file.
        """
        if not os.path.isfile(self._logfile_path):
            self._logfile = io.open(self._logfile_path, mode='a+', encoding=self._logfile_encoding)
            self._logfile_ctime = int(time.time())
            self._logfile.write(u'{0}\n'.format(self._logfile_ctime))
            logging.debug('Create new logfile at: {0}'.format(self._logfile_path))
            return

        self._logfile = io.open(self._logfile_path, mode='a+', encoding=self._logfile_encoding)
        self._get_logfile_ctime()

        if time.time() >= self._logfile_ctime + self._rotation_time:
            self._rotate_logfile()

    def flush(self):

        """
        Flush buffer to file.
        """
        self._logfile.flush()


@provider(ILogObserver)
class ExportToMongodbObserver(object):
    """
    ILogObserver that writes Twisted logger events to a Mongo Database
    
    :param out:     Output stream as sys.stdout or sys.stderr
    :type out:      File object representing Python interpreter standard 
                    output or error stream
    :param format:  Format string suitable for parsing using the Formatter 
                    class (Python format buildin). The log event dictionary
                    is passed to the format function.
    :type format:   String with optional format replacement fields  
    :param datefmt: Date and time format string following strftime convention
    :type datefmt:  string
    """

    def __init__(self, log_cache_size=50, **kwargs):

        self._log_db = db['log']
        self._log_cache_size = log_cache_size

        self._log_cache = []

    def __call__(self, event):
        """
        Add Twisted logger event dictionary to the _log_cache untill
        log_cache_size is reached, then flush to MongoDB
        
        :param event: Twisted logger event
        :type event:  dict
        """

        self._log_cache.append(_serialize_logger_event(event))
        if len(self._log_cache) == self._log_cache_size:
            self.flush()

    def flush(self):
        """
        Flush all log_cache to MongoDB        
        """
        
        # Add cached log records to database
        if len(self._log_cache):
            result = self._log_db.insert_many(self._log_cache)
            if len(result.inserted_ids) == len(self._log_cache):
                logging.info('Inserted {0} log messages in the MongoDB log collection'.format(len(self._log_cache)))
            else:
                logging.error('Unable to insert all log messages to the database')

            self._log_cache = []
