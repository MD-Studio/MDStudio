# -*- coding: utf-8 -*-
import os
import string
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash


def generate_password(password_length=16):
    # type: (int) -> Optional[str]
    """
    Create random password of length `password_length`

    Random characters are picked from the combined collection
    of ascii letters, digits and punctuation marks.

    :param password_length: length of random password
    :return: The password
    """

    # this should not be configurable
    min_length = 12
    # Should not generate passwords smaller then min_length characters
    if password_length < min_length:
        return None

    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    password = ''
    for i in range(password_length):
        # os.urandom is cryptographically strong, so no worries there
        password += chars[ord(os.urandom(1)) % len(chars)]
    return password


def hash_password(password):
    # type: (str) -> str
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
    assert password, "Password must hold a value"

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

    hash_method = '{0}:{1}:{2}'.format(key_derivation, hash_method, hash_iterations)
    return generate_password_hash(password, method=hash_method.lower(), salt_length=salt_length)


def check_password(password_hash, password):
    # type: (str, str) -> bool
    """
    Check plain password against hashed password

    Uses the Werkzeug.security check_password_hash function.

    :param password_hash: hashed password to check against.
    :param password:      plain string password to check
    """

    return check_password_hash(password_hash, password)
