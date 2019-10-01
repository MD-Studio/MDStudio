import binascii
import hashlib
import hmac
import argon2

from passlib.utils import saslprep
from mdstudio.util.exception import MDStudioException

class SCRAM(object):
    @staticmethod
    def create_authentication(password, salt):
        hash_data = argon2.low_level.hash_secret(
            secret=saslprep(password).encode('ascii'),
            salt=salt,
            time_cost=4096,
            memory_cost=512,
            parallelism=1,
            hash_len=32,
            type=argon2.low_level.Type.ID,
            version=0x13,
        )

        _, tag, v, params, _, salted_password = hash_data.decode('ascii').split('$')
        if tag != 'argon2id':
            raise MDStudioException()
        if v != 'v=19':  # argon's version 1.3 is represented as 0x13, which is 19 decimal...
            raise MDStudioException()

        params = {
            k: v
            for k, v in
            [x.split('=') for x in params.split(',')]
        }

        salted_password = salted_password.encode('ascii')
        client_key = hmac.new(salted_password, b"Client Key", hashlib.sha256).digest()
        stored_key = hashlib.new('sha256', client_key).digest()
        server_key = hmac.new(salted_password, b"Server Key", hashlib.sha256).digest()

        return {
            'memory': int(params['m']),
            'kdf': 'argon2id-13',
            'iterations': int(params['t']),
            'salt': binascii.b2a_hex(salt).decode('ascii'),
            'storedKey': binascii.b2a_hex(stored_key).decode('ascii'),
            'serverKey': binascii.b2a_hex(server_key).decode('ascii')
        }
