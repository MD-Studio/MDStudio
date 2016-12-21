# -*- coding: utf-8 -*-

"""
file: management.py

Main user management class
"""

import os
import random
import string
import copy
import time
import hashlib
import socket
import fnmatch

try:
    # Python 3
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse

from   pymongo import MongoClient
from   werkzeug.security import generate_password_hash, check_password_hash
from   twisted.logger import Logger

from   settings import USER_TEMPLATE, PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE, SETTINGS
from   sendmail import Email

# Connect to MongoDB.
# TODO: this should be handled more elegantly
db = None#MongoClient(host='localhost', port=27017)['liestudio']

logging = Logger()

def init_user(settings, config):
    """
    User component bootstrap routines

    Check for the availability of the database user collection
    and add the default admin user if needed

    :param settings: global and module specific settings
    :type settings:  dict or dict like object
    :return:         successful bootstrap completion
    :rtype:          bool
    """

    # @todo: again this should be fixed in a nicer way
    global db
    if db is None:
        db = MongoClient(host=config.get('lie_db.host'), port=config.get('lie_db.port'))['liestudio']

    # Check for MongoDB database
    # TODO: should make a wrapper around PyMongo connection for easy checking connection
    if not db:
        logging.error('Unable to connect to database')
        return False

    # Check if the database has a 'users' collection
    db_collection_name = settings.get('db_collection_name', 'users')
    if db_collection_name not in db.collection_names():
        logging.info('Creating database "{0}" collection'.format(db_collection_name))
    users = db[db_collection_name]

    # Check for admin account (user with uid 0)
    admin = users.find_one({'uid': 0})
    if not admin:
        logging.info('Empty user table. Create default admin account')

        user = UserManager()
        userdata = {'username': settings.get('admin_username', 'admin'),
                    'email': settings.get('admin_email', None),
                    'password': hash_password(settings.get('admin_password', None)),
                    'role': 'admin'}

        admin = user.create_user(userdata)
        if not admin:
            logging.error('Unable to create default admin account')
            return False

    return True


def exit_user(settings):

    """
    User component exit routines

    Terminate all active sessions on component shutdown

    :param settings: global and module specific settings
    :type settings:  dict or dict like object
    :return:         successful exit sequence
    :rtype:          bool
    """

    # Get database
    db_collection_name = settings.get('db_collection_name', 'users')
    users = db[db_collection_name]

    # Count number of active user sessions
    active_session_count = users.find({'session_id': {'$ne': None}}).count()
    logging.debug('{0} active user sessions'.format(active_session_count))

    # Terminate active sessions
    if active_session_count:
        users.update_many({'session_id': {'$ne': None}}, {'$set': {'session_id': None}})
        logging.debug('Terminate {0} active user sessions'.format(active_session_count))

    return True


def generate_password(password_length=10, min_length=8):
    """
    Create random password of length `password_length`
    
    Random characters are picked from the combined collection
    of ascii letters, digits and punctuation marks.
    
    :param password_length: length of random password
    :type password_length:  int
    :param min_length:      not generate passwords with less characters
    :type min_length:       int 
    """

    # Should not generate passwords smaller then min_length characters
    if password_length < min_length:
      logging.warn('Unable to generate password with less then {0} characters ({1})'.format(
        min_length, password_length))
      return

    # Import (pseudo)-random number generator
    try:
        myrg = random.SystemRandom()
    except NotImplementedError:
        logging.debug(
            "Python 'urandom' function not implemented for os: {0} fallback to random.choice()".format(os.name))
        myrg = random.choice

    # Determine character class partitioning based on password_length
    floordiv = password_length // 3
    chargroups = [floordiv] * 3
    chargroups[0] = chargroups[0] + (password_length - (floordiv * 3))

    # Pick random characters from three character collections based on partitioning
    charcollection = (string.ascii_letters, string.digits, string.punctuation)
    password = str().join([ myrg.choice(charcollection[i]) for i,c in enumerate(chargroups) for _ in range(c)])

    logging.debug('Generate {0} character random password: {1}'.format(password_length, password))
    return password


def hash_password(password, key_derivation='pbkdf2', hash_method='sha256', salt_length=10, hash_iterations=1000):
    """
    Hash a password using Werkzeug generate_password_hash method

    Secure hash a password using one of the hash methods supported by Python's
    build-in haslib. Defaults to sha256 with 1000 iterations and the addition
    of a salt string.

    Look at Python's hashlib documentation for information on supported hashing
    algorithms and Werkzeug security documentation on the generate_password_hash
    method.
  
    .. note:: Best to only use hashing methods from the hashlib.algorithms_guaranteed
              collection.

    :param password:        password to hash
    :type password:         string
    :param key_derivation:  key derivation function to use. Defaults to pbkdf2,
                            PBKDF2 (Password-Based Key Derivation Function 2).
    :type key_derivation:   string
    :param hash_method:     secure hash method to use as implemented in
                            Pythons hashlib
    :type hash_method:      string
    :param salt_length:     length of random salt to add to the password hash
    :type salt_length:      int
    :param hash_iterations: number of hash iterations to use
    :type hash_iterations:  int
    """

    if hash_method not in hashlib.algorithms_available:
        logging.debug('Hash method {0} not available. Default to sha256')
        hash_method = 'sha256'

    hash_method = '{0}:{1}:{2}'.format(key_derivation,
                                       hash_method,
                                       hash_iterations)
    password_hash = generate_password_hash(password,
                                           method=hash_method.lower(),
                                           salt_length=salt_length)
    logging.debug('Generate password hash for: {0}, method {1}, salt_length={2}'.format(
        password, hash_method, salt_length))

    return password_hash


def check_password(password_hash, password):
    """
    Check plain password against hashed password

    Uses the Werkzeug.security check_password_hash function.

    :param password:      plain string password to check
    :type password:       string
    :param password_hash: hashed password to check against.
    :type password_hash:  string as returned by hash_password
    :rtype:               bool
    """

    return check_password_hash(password_hash, password)


def is_valid_ipv4_address(address):
    """
    Check validitie of an IPv4 address
    
    :param address: address to check
    :type address:  str
    :rtype:         bool
    """

    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def is_valid_ipv6_address(address):
    """
    Check validitie of an IPv6 address
    
    :param address: address to check
    :type address:  str
    :rtype:         bool
    """

    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True


def resolve_domain(url, scheme=''):
    """
    Resolve a domain of a url irrespective if the url contains a scheme,
    an IP or domain name or a port number
    
    :param url:    url to resolve domain for
    :type url:     str
    :param scheme: scheme of the url, blank by default
    :type scheme:  str
    """

    # Strip the communication schema
    url = url.strip()
    if url.startswith('http://'):
        scheme = 'http://'
        url = url.lstrip('http://')

    # Split on port number if any and parse
    url_spec = urlparse(url.rsplit(':',1)[0], scheme=scheme)
    domain = url_spec.netloc

    # Check if valid ip
    if is_valid_ipv4_address(domain) or is_valid_ipv6_address(domain):
        try:
            domain = socket.gethostbyaddr(domain)[0]
        except:
            pass

    return domain


def ip_domain_based_access(domain, blacklist=[]):
    """
    Filter access based on client IP or domain information.
    If the domain is contained in a domain blacklist return
    False to deny access, otherwise return True.
    
    :param domain:    domain to check access for against black list.
    :type domain:     str
    :param blacklist: domains to blacklist with support for wildcards
    :type blacklist:  list
    
    :rtype:           bool
    """

    for bld in blacklist:
        if fnmatch.fnmatch(domain, bld):
            logging.info('Access for domain {domain} blacklisted (pattern={blacklist})'.format(domain=domain, blacklist=bld))
            return False

    return True


class UserManager(object):
    """
    User management class
    """

    def __init__(self, **kwargs):

        # Get user based on kwargs dictionary.
        # None if no match or unrelated kwargs
        self.user = self.get_user(kwargs)

        # Set the session ID if any
        self.session_id = None
        if self.user:
            self.session_id = self.user.get('session_id', None)

    def set_session_id(self, key):
        """
        Register the WAMP session ID generated by Crossbar in the user object
        and add to the database
        """

        self.session_id = key

        users = db['users']
        users.update_one({'uid': self.user['uid']}, {'$set':{'session_id': self.session_id}})

        logging.debug('Open session: {0} for user {1}'.format(self.session_id, self.user['uid']))

    def retrieve_password(self, email):
        """
        Retrieve password by email
        
        The email message template for user account password retrieval
        is stored in the PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE variable.
        
        * Locates the user in the database by email which should be a 
          unique and persistent identifier.
        * Generate a new random password
        * Send the new password to the users email once. If the email
          could not be send, abort the procedure
        * Save the new password in the database.
        
        :param email: email address to search user for
        :type email:  string
        """

        user = self.get_user({'email': email})
        if not user:
          logging.info('No user with email {0}'.format(email))
          return

        new_password = generate_password()
        user['password'] = hash_password(new_password)
        logging.debug('New password {0} for user {1} send to {2}'.format(new_password, user, email))

        with Email() as email:
          email.send(
            email,
            PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE.format(password=new_password, user=user['username']),
            'Password retrieval request for LIEStudio'
          )
          self.user = user
          self.save()

        return user

    def validate_user_login(self, username, password):
        """
        Validate login attempt for user with password

        :param username: username to check
        :type username:  string
        :param password: password to check
        :type password:  string
        :rtype:          bool
        """

        username = username.strip()
        password = password.strip()

        check = False
        user = self.get_user({'username': username})
        if user:
            check = check_password(user['password'], password)
        else:
            logging.debug('No such user')

        logging.info('{status} login attempt for user: {user}',
            status='Correct' if check else 'Incorrect', user=username)

        return check

    def user_logout(self):
        """
        Logout user by clearing session_id

        :return: successful logout
        :rtype:  bool
        """

        if self.user and self.user.get('session_id', None) != None:
            users = db['users']
            users.update_one({'session_id': self.user['session_id']}, {'$set': {'session_id': None}})

            logging.info('Logout user: {0}, uid: {1}'.format(self.user['username'], self.user['uid']))
            self.user = None
            return True

        return False

    def create_user(self, userdata, required=['username', 'email']):
        """
        Create new user and add to database
        """

        user_template = copy.copy(USER_TEMPLATE)
        users = db['users']

        # Require at least a valid username and email
        for param in required:
            if not userdata.get(param, None):
                logging.error('Unable to create new user. Missing "{0}"'.format(param))
                return

        # If no password, create random one
        if not userdata.get('password', None):
            random_pw = generate_password()
            user_template['password'] = hash_password(random_pw)

        user_template.update(userdata)

        # Username and email should not be in use
        if users.find_one({'username': userdata['username']}):
            logging.error('Username {0} already in use'.format(userdata['username']))
            return
        if users.find_one({'email': userdata['email']}):
            logging.error('Email {0} already in use'.format(userdata['email']))
            return

        # Make new uid, increment max uid by 0
        uid = users.find_one(sort=[("uid", -1)])
        if not uid:
            uid = 0
        else:
            uid = uid['uid']
            uid += 1
        user_template['uid'] = uid

        # Add the new user to the database
        did = users.insert_one(user_template).inserted_id
        if did:
            logging.debug('Added new user to database. user: {username}, uid: {uid}'.format(**user_template))
        else:
            logging.error('Unable to add new user to database')
            return

        return user_template

    def remove_user(self, userdata):
        """
        Remove a user from the database

        :param userdata: PyMongo style database query
        :type userdata:  dict
        """

        user = self.get_user(userdata)
        if not user:
            logging.error('No such user to remove: {0}'.format(
                ' '.join(['{0},{1}'.format(*item) for item in userdata.items()])))
            return False
        else:
            logging.info('Removing user "{username}", with uid {uid} from database'.format(**user))
            db['users'].delete_one(user)

        return True

    def get_safe_user(self, query, remove=('password', '_id')):
        """
        Equal to get_user but with sensitive and non-serializable data removed

        :param query: PyMongo style database query
        :return:      dict
        """

        user = self.get_user(query)

        for entry in remove:
            if entry in user:
                del user[entry]

        return user

    def get_user(self, query):
        """
        Get user data by query

        :param query: PyMongo style database query
        :type query:  dict
        """
        global db
        users = db['users']
        result = users.find_one(query)

        return result

    def save(self):
        """
        Save modified user data to database
        """

        if self.user:
          users = db['users']
          users.replace_one({'_id':self.user['_id']}, self.user)
