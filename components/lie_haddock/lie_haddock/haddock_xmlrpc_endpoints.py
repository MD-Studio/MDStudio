# -*- coding: utf-8 -*-

"""
Provides an interface for HADDOCK XML-RPC endpoints

Author: Mikael Trellet (Utrecht University)
        Marc van Dijk (VU Amsterdam)
"""

import os
import sys
import xmlrpclib
import hashlib
import logging
import tarfile

if sys.version_info[0] < 3:
    from urllib2 import urlopen
else:
    from urllib import urlopen


class HaddockXmlrpcException(Exception):
    """
    Haddock XML-RPC specific Exception class logging errors
    """

    def __init__(self, message, user):

        logging.error('Haddock XML-RPC error for user "{0}": {1}'.format(user, message))


class HaddockXmlrpcInterface(object):

    def __init__(self, server_url=None, username=None, password=None):
        """
        Register server XML-RPC endpoint URL, username and md5 hashed password
        
        :param server_url: Haddock XML-RPC endpoint URL
        :type server_url:  :py:str
        :param username:   Haddock server user name
        :type username:    :py:str
        :param password:   Haddock server user password
        :type password:    :py:str 
        """

        self.url = server_url
        self.server = xmlrpclib.Server(server_url)
        self.username = username
        self.password = hashlib.md5(password).hexdigest()
        
        self.authenticated = False

    def login(self):
        """
        Login with HADDOCK username and password
        """

        if not self.authenticated:
            try:
                user = self.server.checkUser(self.username, self.password)
                if user:
                    logging.debug('Successful authentication of use "{0}" at {1}'.format(self.username, self.url))
                    self.authenticated = True
            except xmlrpclib.Fault, e:
                HaddockXmlrpcException(e.faultString, self.username)
                self.authenticated = False

        return self.authenticated

    def logout(self):
        """
        Logout
        """

        logging.debug('Logout user: {0}'.format(self.username))

        self.username = ''
        self.password = ''
        self.authenticated = False

    def list_users(self):
        """
        List HADDOCK users by username and password

        Only if the user making the call is authorized to make the request
        """

        if not self.login():
            return

        try:
            return self.server.listUsers(self.username, self.password)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)

    def list_projects(self):
        """
        List HADDOCK projects (finished or not)
        """

        if not self.login():
            return

        try:
            return self.server.listAllProjects(self.username, self.password)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)
            return []

    def get_status(self, project):
        """
        Get the status of a (running) project

        :param project: Project ID to get status for
        :type project:  :py:str

        :return:        Project status as 'processing', 'done' or 'error'
        :rtype:         :py:str
        """

        if not self.login():
            return

        try:
            return self.server.getProjectStatus(self.username, self.password, project)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)
            return {}

    def get_results_url(self, project):
        """
        Get results .tgz archive download location

        :param project:
        :return:
        """

        if not self.login():
            return

        try:
            return self.server.getResultsDownloadLocation(self.username, self.password, project)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)
            return None

    def get_params(self, project):
        """
        Get Haddock project .web parameter file

        :param project:
        :return:
        """

        if not self.login():
            return

        try:
            return self.server.getProjectParams(self.username, self.password, project)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)
            return None

    def get_results(self, project, target, untar=True, remove_tgz=True):
        """
        Download results .tgz archive for a project

        :param project:    Project name to download
        :type project:     :py:str
        :param target:     Target dir or absolute file path to download to
        :type target:      :py:str
        :param untar:      Extract the tar file (tgz)
        :type untar:       :py:bool
        :param remove_tgz: Remove the tar archive after unpacking
        :type remove_tgz:  :py:bool

        :return:           Result file path
        :rtype:            :py:str
        """

        url = self.get_results_url(project)
        if not url:
            HaddockXmlrpcException('Haddock results for {0} not found or not available yet: {0}'.format(project),
                                   self.username)
            return

        u = urlopen(url)
        file_name = url.split('/')[-1]
        target = os.path.abspath(target)

        # Prepare target file path
        if os.path.isdir(target):
            target = os.path.join(target, file_name)
        if not os.path.isdir(os.path.dirname(target)):
            HaddockXmlrpcException('Download directory does not exisit: {}'.format(target), self.username)
            return

        target = '{0}{1}'.format(os.path.splitext(target)[0], os.path.splitext(file_name)[1])
        download_file = open(target, 'wb')

        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        logging.debug('Downloading: {0} Bytes: {1}'.format(file_name, file_size))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            download_file.write(buffer)
        download_file.close()

        if os.path.isfile(target):
            logging.debug('Successfully downloaded results archive {0}'.format(target))

            if untar:
                tar = tarfile.open(target, 'r')
                for item in tar:
                    tar.extract(item, os.path.dirname(target))

                # Check if archive unpacked and remove tgz file
                if os.path.isdir(os.path.splitext(target)[0]):
                    if remove_tgz:
                        os.remove(target)
                    target = os.path.splitext(target)[0]

        else:
            HaddockXmlrpcException('Unable to download result {0}'.format(target), self.username)
            return None

        return target

    def launch_project(self, params, project):
        """
        Launch a Haddock project by uploading a .web parameter file

        :param params:  Haddock .web parameter file
        :type params:   :py:str
        :param project: project name
        :type project:  :py:str

        :return:        project name
        """

        if not self.login():
            return

        try:
            return self.server.launchProject(self.username, self.password, project, params)
        except xmlrpclib.Fault, e:
            HaddockXmlrpcException(e.faultString, self.username)
            return None
