# -*- coding: utf-8 -*-

"""
file: test.py

Unit tests for the user component

TODO: Add wamp_services unittests
"""
import timeit

import os
import sys

import random
import unittest2
import hashlib
import string
import shutil

# Test import of the lie_db database drivers
# If unable to import we cannot run the UserDatabaseTests
dbenabled = False
try:
    from lie_db import BootstrapMongoDB

    dbenabled = True
except BaseException:
    pass

from lie_user.management import generate_password, hash_password, check_password, UserManager


@unittest2.skipIf(dbenabled == False, "Not supported, no active LIE MongoDB.")
class UserDatabaseTests(unittest2.TestCase):
    """
    Unittest user management component

    A reference database with user collection is created in the test directory
    containing 4 users named test1 to test4 with passwords equal to the username
    and email adresses test1@email.com to test4@email.com
    """

    _mongodb_database_name = 'unittest_db'
    _currpath = os.path.abspath(__file__)
    _dbpath = os.path.join(os.path.dirname(_currpath), _mongodb_database_name)
    _dblog = os.path.join(os.path.dirname(_currpath), '{0}.log'.format(_mongodb_database_name))

    @classmethod
    def setUpClass(cls):
        """
        UserDatabaseTests class setup

        * Bootstrap MongoDB with an empty test database
        * Write MongoDB log to local mongodb.log file
        """

        # Start the database
        cls.db = BootstrapMongoDB(dbpath=cls._dbpath,
                                  dbname='liestudio',
                                  dblog=cls._dblog)
        cls.db.start()

        # Add users in bulk using default PyMongo functions
        client = cls.db.connect()
        user = client['users']
        user.insert_many([
            {'username': 'test1', 'email': 'test1@email.com', 'password': hash_password('test1'), 'role': 'default',
             'uid': 0, 'session_id': None},
            {'username': 'test2', 'email': 'test2@email.com', 'password': hash_password('test2'), 'role': 'default',
             'uid': 1, 'session_id': None},
            {'username': 'test3', 'email': 'test3@email.com', 'password': hash_password('test3'), 'role': 'default',
             'uid': 2, 'session_id': None},
            {'username': 'test4', 'email': 'test4@email.com', 'password': hash_password('test4'), 'role': 'default',
             'uid': 3, 'session_id': None},
        ])

    @classmethod
    def tearDownClass(cls):
        """
        UserDatabaseTests class teardown

        * Disconnect from MongoDB
        * Stop mongod process
        * Remove MongoDB test database and logfiles
        """

        cls.db.stop(terminate_mongod_on_exit=True)

        if os.path.exists(cls._dbpath):
            shutil.rmtree(cls._dbpath)
        if os.path.exists(cls._dblog):
            os.remove(cls._dblog)

    def test_create_user_unsufficient_data(self):
        """
        Unable to create a new user if not at least a username
        and email adress are defined.
        """

        user = UserManager()
        self.assertIsNone(user.create_user({'username': 'test'}))

    def test_create_user(self):
        """
        Test addition of a user
        """

        userdata = {'username': 'test5', 'email': 'test5@email.com'}
        user = UserManager()

        # Create new user with random password
        newuser = user.create_user(userdata)
        self.assertTrue(len(newuser))
        self.assertEqual(newuser['username'], userdata['username'])
        self.assertEqual(newuser['email'], userdata['email'])

        self.assertTrue(user.remove_user({'username': 'test5', 'email': 'test5@email.com'}))

    def test_create_user_uniqueuser(self):
        """
        Test addition of unique user with respect to username
        and password
        """

        # Try adding user that already exists
        user = UserManager()
        self.assertIsNone(user.create_user({'username': 'test3', 'email': 'test3@email.com'}))

    def test_remove_user(self):
        """
        Test removal of a user from the database
        """

        user = UserManager()
        self.assertTrue(user.remove_user({'username': 'test4', 'email': 'test4@email.com'}))

    def test_validate_user_login(self):
        """
        Test user login attempts
        """

        user = UserManager()
        self.assertTrue(user.validate_user_login('test1', 'test1'))
        self.assertFalse(user.validate_user_login('test2', 'bar'))

    def test_get_user_info(self):
        """
        Test user information from the database.
        All data and 'safe' data
        """

        user = UserManager()
        self.assertEqual(user.get_safe_user({'username': 'test1'}),
                         {'email': 'test1@email.com', 'session_id': None, 'username': 'test1', 'role': 'default',
                          'uid': 0})

    def test_user_password_retrieval(self):
        """
        Test user lost/forgotten password retrieval

        Test searches user by email, generates new password, sends password to
        user by mail and changes password in user database record if the email
        was successfully send.
        This test will fail if the email server is not configured correctly.
        """

        user = UserManager(email='test2@email.com')
        current_password = user.user['password']

        user.retrieve_password('test2@email.com')
        self.assertNotEqual(user.user['password'], current_password)


class UserTests(unittest2.TestCase):
    """
    Unittest user management component
    """

    def test_password_generation_minlength(self):
        """
        Unable to generate passwords with less then `min_length` chars
        """

        self.assertIsNone(generate_password(6))

    def test_password_generation_length(self):
        """
        Test random password generation with a length of `password_length` characters
        """

        # +10 for the minimum password length
        for pw_length in [10+int(100*random.random()) for i in range(100)]:
            password = generate_password(pw_length)
            self.assertTrue(len(password), pw_length)


    def test_password_hash_time(self):
        htime = timeit.timeit(lambda: hash_password("test_password"), number=10) / 10
        self.assertGreater(htime, 0.1)

    def test_password_generation_randomcharselection(self):
        """
        Random password should be strong, contain letters, digits and punctuations
        """

        randpw = generate_password(10)
        strongpw = all([len(set(randpw).intersection(set(charset))) != 0 for
                        charset in (string.ascii_letters, string.digits, string.punctuation)])
        self.assertTrue(strongpw)

    def test_password_hashing_checking(self):
        """
        Test password hashing and hash checking using often used
        hashing algorithms
        """

        pw = 'Te#%ghTdkk'
        hashed = hash_password(pw)
        self.assertTrue(check_password(hashed, pw))
