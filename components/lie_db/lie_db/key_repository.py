import base64
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pymongo import ReturnDocument

from mdstudio.db.connection_type import ConnectionType
from mdstudio.db.exception import DatabaseException


class KeyRepository(object):
    _internal_db = None

    def __init__(self, session, internal_db):
        self._session = session
        self._internal_db = internal_db

    def get_key(self, claims):
        connection_type = claims['connectionType']
        model = self._get_key_model(connection_type)
        body = self._get_key_body(claims, connection_type)
        found = model.find_one(body)
        if not found:
            new_key = self._new_key()
            # find_one_and_update ensures transactionality here
            found = self._get_key_model(connection_type).find_one_and_update(body, {
                '$setOnInsert': new_key
            }, upsert=True, return_document=ReturnDocument.AFTER)
        return self._decrypt_key(found['key'])

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

    def _new_key(self):

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
        try:
            return self._get_session_crypto().decrypt(password)
        except InvalidToken:
            raise DatabaseException('Tried to decrypt the component key with a different secret! Please use your old secret.')

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
            request['role'] = claims['role']
        else:
            raise NotImplemented('This distinction does not exist')
        return request
