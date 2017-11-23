import base64
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pymongo import ReturnDocument

from mdstudio.db.connection import ConnectionType
from mdstudio.db.model import Model


class KeyRepository(object):
    class Key(Model):
        pass

    _internal_db = None

    def __init__(self, session, internal_db):
        self._session = session
        self._internal_db = internal_db

    def get_key(self, claims):
        connection_type = claims['connectionType']
        password = self._new_password()
        print("CALL")
        result = self._get_key_model(connection_type).find_one_and_update(self._get_key_body(claims, connection_type), {
            '$setOnInsert': password
        }, upsert=True, return_document=ReturnDocument.AFTER)
        return self._decrypt_key(result['key'])

    def _key_from_password(self, password, salt):
        kdf = PBKDF2HMAC(
             algorithm=hashes.SHA256(),
             length=32,
             salt=salt,
             iterations=150000,
             backend=default_backend()
         )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def _new_password(self):

        key = self._key_from_password(Fernet.generate_key(), os.urandom(16))
        return {
            'key': self._encrypt_key(key),
        }

    def _encrypt_key(self, password):
        value = self._get_session_crypto().encrypt(password)
        del password
        return value

    def _get_session_crypto(self):
        return Fernet(self._session.secret)

    def _decrypt_key(self, password):
        return self._get_session_crypto().decrypt(password)

    def _get_key_model(self, connection_type):
        return self._internal_db._db['{}.keys'.format(connection_type)]

    def _get_key_body(self, claims, connection_type):
        request = {
            'type': connection_type
        }
        connection_type = ConnectionType.from_string(connection_type)
        if connection_type == ConnectionType.User:
            request['username'] = claims['username']
        elif connection_type == ConnectionType.Group:
            request['group'] = claims['group']
        elif connection_type == ConnectionType.GroupRole:
            request['group'] = claims['group']
            request['groupRole'] = claims['groupRole']
        else:
            raise NotImplemented('This distinction does not exist')
        return request
