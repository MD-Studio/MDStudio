import os
from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC

from passlib.hash import scram
from passlib.utils import xor_bytes


class SCRAM(object):
    @staticmethod
    def split_authid(authid):
        auth = authid.split('~', 1)
        return auth[0], auth[1]

    @classmethod
    def client_nonce(cls):
        return cls.binary_to_str(os.urandom(24))

    @classmethod
    def authid(cls, username):
        client_nonce = cls.client_nonce()
        return u'{}~{}'.format(username, client_nonce), client_nonce

    @staticmethod
    def binary_to_str(binary):
        return b64encode(binary).decode('utf8')

    @staticmethod
    def str_to_binary(data):
        return b64decode(data.encode('utf8'))

    @classmethod
    def salted_password(cls, password, salt=None, iterations=656000):
        if salt is None:
            salt = cls.binary_to_str(os.urandom(16))

        salted_password = scram.derive_digest(password, salt.encode('utf8'), iterations, 'sha256')

        return salt, iterations, salted_password

    @staticmethod
    def auth_message(client_nonce, server_nonce):
        return u'{}.{}'.format(client_nonce, server_nonce).encode('utf8')

    @staticmethod
    def stored_key(client_key):
        return sha256(client_key).digest()

    @classmethod
    def client_key(cls, salted_password):
        return cls._hmac(salted_password, b'Client Key')

    @classmethod
    def server_key(cls, salted_password):
        return cls._hmac(salted_password, b'Server Key')

    @classmethod
    def client_signature(cls, stored_key, auth_message):
        return cls._hmac(stored_key, auth_message)

    @staticmethod
    def client_proof(client_key, client_signature):
        return xor_bytes(client_key, client_signature)

    @classmethod
    def server_proof(cls, server_key, auth_message):
        return cls._hmac(server_key, auth_message)

    @classmethod
    def server_signature(cls, server_key, auth_message):
        return cls._hmac(server_key, auth_message)

    @classmethod
    def authenticate_client(cls, client_signature, client_proof, stored_key):
        return cls.client_proof(client_proof, client_signature) == stored_key

    @staticmethod
    def authenticate_server(server_signature, server_response):
        return server_response == server_signature

    @staticmethod
    def _hmac(key, message):
        return HMAC(key, message).digest()
