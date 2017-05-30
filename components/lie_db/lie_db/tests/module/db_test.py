# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the db component
"""

import os
import shutil
import unittest
import logging
import glob

from lie_db.db_methods import BootstrapMongoDB

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')


class DatabaseTest(unittest.TestCase):

    """
    Unittest MongoDB bootstrapping
    """

    def setUp(self):

        currpath = os.path.abspath(__file__)

        self.dblog = os.path.join(os.path.dirname(currpath), 'mongodb.log')
        self.db = BootstrapMongoDB('unittest_db', dbname='liestudio', dblog=self.dblog)

    @unittest.skipIf(os.getenv('IS_DOCKER', False), "In the docker version, we always run mongodb")
    def test_start_stop_local_database(self):
        """
        Test start/stop of a local MongoDB server and load of
        the application database
        """

        # Start the Database
        self.assertTrue(self.db.start())
        self.assertTrue(os.path.exists(self.db._dbpath))

        # Check for/create application database document
        db = self.db.connect()
        appdata = db['liestudio_data'].find_one()
        self.assertTrue(len(appdata))

        # Stop the Database
        self.assertTrue(self.db.stop())

    @unittest.skipIf(os.getenv('IS_DOCKER', False), "In the docker version, we always run mongodb")
    def test_not_running_database(self):
        """
        Test connecting to a MongoDB server that does not exist
        """

        self.assertFalse(self.db.isrunning)
        self.assertFalse(self.db.isremote)
        self.assertFalse(len(self.db.info))

    @unittest.skipIf(os.getenv('IS_DOCKER', False), "In the docker version, we always run mongodb")
    def test_running_database(self):
        """
        Test connecting to a MongoDB server that exists
        """

        self.db = BootstrapMongoDB('unittest_db', dbname='liestudio', dblog=self.dblog)

        # Start the test database
        self.assertTrue(self.db.start())

        # Test if it is running
        self.assertTrue(self.db.isrunning)
        self.assertFalse(self.db.isremote)
        self.assertTrue(len(self.db.info))

        # Stop the database
        self.assertTrue(self.db.stop())

    def tearDown(self):
        """
        Cleanup temporary MongoDB database files after unittest.
        """

        if os.path.exists('unittest_db'):
            shutil.rmtree('unittest_db')
        for log in glob.glob('mongodb.log*'):
            os.remove(log)
