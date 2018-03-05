# -*- coding: utf-8 -*-

"""
file: settings.py

User module wide settings
"""

SETTINGS = {
    'random_password_length': 10,
    'key_derivation':         'pbkdf2',
    'has_method':             'sha256',
    'salt_length':            10,
    'hash_iteration':         1000,
    'db_collection_name':     'users',
    'admin_username':         'lieadmin',
    'admin_email':            'm4.van.dijk@vu.nl',
    'admin_password':         'liepw@#',
    'email_smtp_server':      'smtp.gmail.com',
    'email_smtp_port':        587,
    'email_smtp_username':    'marcvdijk@gmail.com',
    'email_smtp_password':    '<password>',
    'email_smtp_usetls':      None,
    'only_localhost_access':  False,
    'domain-blacklist':       []
}

USER_TEMPLATE = {
    'username': None,
    'email': None,
    'password': None,
    'role': 'user',
    'uid': 0,
    'session_id': None
}

PASSWORD_RETRIEVAL_MESSAGE_TEMPLATE = """
Dear {user},

We have recieved a password retrieval request for your LIEStudio account.
Your new password is:

    {password}

Best regards,

The LIEStudio team
"""
