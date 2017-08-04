# -*- coding: utf-8 -*-

"""
file: email.py

Emailing users
"""

import smtplib

from email.mime.text import MIMEText
from twisted.logger import Logger

logging = Logger()


class Email(object):

    def __init__(self, email_sender='info@mdstudio.vu.nl', email_smtp_server='127.0.01', email_smtp_port=1025,
                 email_smtp_usetls=None, email_smtp_username=None, email_smtp_password=None):
        """
        Email class using Python's buildin SMTP server (smtplib)
        for handling email message relay.

        The SMTP server needs to be configured with a valid smtp
        server address and port number.

        .. note:: If Using Gmail as server, check if "access from less secured
                  Apps" is turned off in account preferences otherwise login
                  is not accepted.

        :param email_sender:        "send from" and "reply to" email address
        :type email_sender:         string
        :param email_smtp_server:   SMTP server IP or domain name
        :type email_smtp_server:    string
        :param email_smtp_port:     SMTP server port number
        :type email_smtp_port:      int
        :param email_smtp_usetls:   rather to use secured message transport protocol over TLS
                                    None, will activate TLS automatically for port numbers
                                    443,465,993 and 995.
        :type email_smtp_usetls:    bool or None
        :param email_smtp_username: sender email account user name
        :type email_smtp_username:  string
        :param email_smtp_password: sender email account password
        :type email_smtp_password:  string
        """

        self.email_sender = email_sender
        self.smtp_server = None

        try:
            self.smtp_server = smtplib.SMTP(email_smtp_server, email_smtp_port)
            self.smtp_server.ehlo()

            if email_smtp_usetls or port in (443, 465, 993, 995):
                self.smtp_server.starttls()

            self.smtp_server.login(email_smtp_username, email_smtp_password)
        except Exception as e:
            logging.error('{0} Unable to establish SMTP server connection to {1}:{2}'.format(type(e),
                                                                                             email_smtp_server, email_smtp_port))

    def __enter__(self):
        """
        Implement class __enter__
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Implement class __exit__

        Close the smtp server
        """

        self.smtp_server_close()

    def send(self, emails, message, subject):
        """
        Composing and sending email messages

        Supports sending emails to one or multiple recipients

        :param emails:  one or more recipient email addresses
        :type emails:   string or list of strings
        :param message: message body
        :type message:  string
        :param subject: email message subject
        :type subject:  string
        """

        if self.smtp_server:
            if not isinstance(emails, list):
                emails = [emails]

            for email in emails:
                msg = MIMEText(message)
                msg['Subject'] = subject
                msg['From'] = self.email_sender
                msg['To'] = email

                self.smtp_server.send_message(msg)

    def smtp_server_close(self):
        """
        Close connection to the smtp server
        """

        if self.smtp_server:
            self.smtp_server.quit()
