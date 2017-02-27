# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the user component

TODO: Add wamp_services unittests
"""

import os, sys
import unittest2
import shutil
import time
import glob

# Add modules in package to path so we can import them
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from   twisted.logger import Logger, globalLogPublisher, LogLevel, LogLevelFilterPredicate, FilteringLogObserver

# Test import of the lie_db database drivers
# If unable to import we cannot run the UserDatabaseTests
dbenabled = False
try:
  from lie_db import BootstrapMongoDB
  dbenabled = True
except:
  pass

from lie_logger.system_logger import *

logging = Logger()

@unittest2.skipIf(dbenabled == False, "Not supported, no active LIE MongoDB.")
class LoggerExportToMongodbObserverTest(unittest2.TestCase):
  
  observer = None
  _mongodb_database_name = 'unittest_db'
  _currpath = os.path.abspath(__file__)
  _dbpath = os.path.join(os.path.dirname(_currpath), _mongodb_database_name)
  _dblog = os.path.join(os.path.dirname(_currpath), '{0}.log'.format(_mongodb_database_name))
  
  @classmethod
  def setUpClass(cls):
      """
      LoggerExportToMongodbObserverTest class setup
      
      * Bootstrap MongoDB with an empty test database
      * Write MongoDB log to local mongodb.log file
      """
      
      # Start the database
      cls.db = BootstrapMongoDB(dbpath=cls._dbpath,
                                dbname='liestudio',
                                dblog=cls._dblog)
      cls.db.start()
      
      filter_predicates = [
        LogLevelFilterPredicate(defaultLogLevel=LogLevel.levelWithName('info'))
      ]
      
      cls.observer = FilteringLogObserver(observer=ExportToMongodbObserver(log_cache_size=10), predicates=filter_predicates)
      globalLogPublisher.addObserver(cls.observer)
  
  @classmethod
  def tearDownClass(cls):
      """
      LoggerExportToMongodbObserverTest class teardown

      * Disconnect from MongoDB
      * Stop mongod process
      * Remove MongoDB test database and logfiles
      """
      
      globalLogPublisher.removeObserver(cls.observer)
      cls.db.stop(terminate_mongod_on_exit=True)
      
      if os.path.exists(cls._dbpath):
          shutil.rmtree(cls._dbpath)
      if os.path.exists(cls._dblog):
          os.remove(cls._dblog)
  
  def test_exporttomongodbobserver_loglevel(self):
      
      # empty db log collection
      client = self.db.connect()
      client['log'].remove()
      
      for logmessage in range(4):
        logging.debug('Logging debug message {0}'.format(logmessage))
        logging.info('Logging info message {0}'.format(logmessage))
        logging.warn('Logging warn message {0}'.format(logmessage))
        logging.error('Logging error message {0}'.format(logmessage))
        logging.critical('Logging critical message {0}'.format(logmessage))
      
      self.assertEqual(set([n['log_level'] for n in client['log'].find()]), {'info', 'warn', 'error', 'critical'})
      
  def test_exporttomongodbobserver_messages(self):
      """
      When logging messages to the MongoDB database, the structured
      log messages are added to the db collection in batches of 10
      (log_cache_size argument to the observer).
      
      Thus after logging 15 messages, 10 will be available in the db
      when we look for it, all logged at 'info' level
      """
    
      # empty db log collection
      client = self.db.connect()
      client['log'].remove()
      
      for logmessage in range(15):
        logging.info('Logging info message {0}'.format(logmessage))
      
      # With a cache size of 10, there should be 10 log messages in the db
      self.assertTrue(client['log'], 10)
      
      # Get one message and inspect
      logmessage = client['log'].find().sort('_id',-1)[0];
      self.assertIsNotNone(logmessage)
      if logmessage:
        self.assertEqual(logmessage['log_level'], 'info')
        self.assertEqual(logmessage['log_namespace'], 'tests.module_test')

class LoggerRotateFileLogObserverTest(unittest2.TestCase):
  
  observer = None
  _currpath = os.path.abspath(__file__)
  _logfilepath = os.path.join(os.path.dirname(_currpath), 'rotatelogfile.log')
  
  @classmethod
  def setUpClass(cls):
      """
      LoggerRotateFileLogObserverTest class setup
      
      Init Twisted logger with RotateFileLogObserver logger
      """
      
      filter_predicates = [
        LogLevelFilterPredicate(defaultLogLevel=LogLevel.levelWithName('info'))
      ]
      
      cls.observer = FilteringLogObserver(observer=RotateFileLogObserver(logfile_path=cls._logfilepath, rotation_time=4), 
        predicates=filter_predicates)
      globalLogPublisher.addObserver(cls.observer)
  
  @classmethod
  def tearDownClass(cls):
      """
      LoggerRotateFileLogObserverTest class teardown

      Remove RotateFileLogObserver from Twisted globalLogPublisher
      and remove logfile.
      """
    
      globalLogPublisher.removeObserver(cls.observer)
      for logfile in glob.glob('{0}/rotatelogfile*.log'.format(os.path.dirname(cls._currpath))):
        os.remove(logfile)
  
  def test_rotationfileobserver_timerotation(self):
      """
      This test class configures the RotateFileLogObserver to 
      create a new log file after every 4 seconds past.
      
      Logging a series of messages 4 times with 4 seconds delay
      between each should give at minimum 4 logfiles
      """
    
      for logmessage in range(4):
        logging.debug('Logging debug message {0}'.format(logmessage))
        logging.info('Logging info message {0}'.format(logmessage))
        logging.warn('Logging warn message {0}'.format(logmessage))
        logging.error('Logging error message {0}'.format(logmessage))
        logging.critical('Logging critical message {0}'.format(logmessage))
        time.sleep(5)
      
      logfiles = glob.glob('{0}/rotatelogfile*.log'.format(os.path.dirname(self._currpath)))
      self.assertTrue(len(logfiles) >= 4)
      
class LoggerPrintingObserverTest(unittest2.TestCase):
  
  observer = None
  
  @classmethod
  def setUpClass(cls):
      """
      LoggerPrintingObserverTest class setup
      
      Init Twisted logger with PritingObserver logger
      """
      
      filter_predicates = [
        LogLevelFilterPredicate(defaultLogLevel=LogLevel.levelWithName('debug'))
      ]
      
      cls.observer = FilteringLogObserver(observer=PrintingObserver(), predicates=filter_predicates)
      globalLogPublisher.addObserver(cls.observer)
  
  @classmethod
  def tearDownClass(cls):
      """
      LoggerPrintingObserverTest class teardown

      Remove PrintingObserver from Twisted globalLogPublisher 
      """
    
      globalLogPublisher.removeObserver(cls.observer)
  
  def test_printingobserver_loglevels(self):
    
      d = logging.info('log message')