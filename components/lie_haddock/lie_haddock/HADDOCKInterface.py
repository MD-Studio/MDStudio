"""
Provides an interface for HADDOCK XMLRPC endpoint

Author: {0} ({1})
"""

import xmlrpclib
import hashlib
import getpass

__author__ = "Mikael Trellet"
__email__ = "mikael.trellet@gmail.com"


class HADDOCKInterface:

    def __init__(self, server_url='http://milou.science.uu.nl/cgi/services/HADDOCK2.2/haddockserver-xmlrpc.cgi'):
        self.url = server_url
        self.server = xmlrpclib.Server(server_url)
        self.usr = ''
        self.passwd = ''
        self.authenticated = False

    def login(self):
        """ Login with HADDOCK username and password """
        try:
            usr = raw_input("Username: ")
            passwd = hashlib.md5(getpass.getpass("Password: ")).hexdigest()
            user = self.server.checkUser(usr, passwd)
            if user:
                self.usr = usr
                self.passwd = passwd
                self.authenticated = True
        except:
            self.authenticated = False
            raise

    def logout(self):
        """ Logout """
        self.usr = ''
        self.passwd = ''
        self.authenticated = False

    def list_users(self):
        """ List HADDOCK users by username and password """

        if not self.authenticated:
            try:
                self.login()
            except:
                raise

        try:
            users = self.server.listUsers(self.usr, self.passwd)
        except:
            raise
        return users

    def list_projects(self):
        """ List HADDOCK projects (finished or not) """
        if not self.authenticated:
            try:
                self.login()
            except:
                raise
        try:
            projects = self.server.listAllProjects(self.usr, self.passwd)
        except:
            raise
        return projects

    def get_status(self, project):
        if not self.authenticated:
            try:
                self.login()
            except:
                raise
        try:
            status = self.server.getProjectStatus(self.usr, self.passwd, project)
        except:
            raise
        return status

    def get_url(self, project):
        if not self.authenticated:
            try:
                self.login()
            except:
                raise
        try:
            url = self.server.getResultsDownloadLocation(self.usr, self.passwd, project)
        except:
            raise
        return url

    def get_params(self, project):
        if not self.authenticated:
            try:
                self.login()
            except:
                raise
        try:
            haddockparams = self.server.getProjectParams(self.usr, self.passwd, project)
        except:
            raise
        return haddockparams

    def launch_project(self, params, project):
        if not self.authenticated:
            try:
                self.login()
            except:
                raise
        try:
            output = self.server.launchProject(self.usr, self.passwd, project, params)
        except:
            raise
        return output