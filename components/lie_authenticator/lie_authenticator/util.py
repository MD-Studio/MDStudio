# -*- coding: utf-8 -*-

"""
file: util.py

Utility functions for authentication
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

from werkzeug.security import generate_password_hash, check_password_hash
from twisted.logger import Logger

from .sendmail import Email

logging = Logger()


def generate_password(password_length=12):
    """
    Create random password of length `password_length`

    Random characters are picked from the combined collection
    of ascii letters, digits and punctuation marks.

    :param password_length: length of random password
    :type password_length:  int
    """

    # this should not be configurable
    min_length = 10
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
    password = str().join([myrg.choice(charcollection[i]) for i, c in enumerate(chargroups) for _ in range(c)])

    logging.debug('Generate {0} character random password: {1}'.format(password_length, password))
    return password


def hash_password(password):
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
    """

    # these are not parameters on purpose.
    # we should be sure the defaults are chosen securely
    # with these configuration set we take at least 0.05s
    # to derive a hash, which should give us some protection
    # when our database leaks.
    key_derivation = 'pbkdf2'
    hash_method = 'sha512'
    # salt length should be approx 512/8 bytes
    salt_length = 64
    hash_iterations = 656000
    if hash_method not in hashlib.algorithms_available:
        logging.debug('Hash method {0} not available. Default to sha512')
        hash_method = 'sha512'

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
    url_spec = urlparse(url.rsplit(':', 1)[0], scheme=scheme)
    domain = url_spec.netloc

    # Check if valid ip
    if is_valid_ipv4_address(domain) or is_valid_ipv6_address(domain):
        try:
            domain = socket.gethostbyaddr(domain)[0]
        except BaseException:
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

