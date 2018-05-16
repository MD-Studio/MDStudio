# -*- coding: utf-8 -*-

"""
file: module_server_communication_test.py

Unit tests for XML-RPC communication with the Haddock server
"""

import os
import unittest2
import pkg_resources
import shutil
import time

from lie_graph.graph_io.io_jsonschema_format import read_json_schema
from lie_graph.graph_io.io_web_format import read_web
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools

from lie_haddock.haddock_xmlrpc_endpoints import HaddockXmlrpcInterface
from lie_haddock.haddock_helper_methods import resolve_credentials

# Parse package configuration file
settings_file = pkg_resources.resource_filename('lie_haddock', '/schemas/settings.json')
xmlrpc_settings = read_json_schema(settings_file)
xmlrpc_settings.node_tools = NodeAxisTools
settings = xmlrpc_settings.getnodes(xmlrpc_settings.root).settings

server_username, server_password = resolve_credentials(settings)


@unittest2.skipIf(server_username is None and server_password is None,
                  "HADDOCK_SERVER_USER and HADDOCK_SERVER_PW environment variables not set.")
class TestHaddockServerCommunication(unittest2.TestCase):

    filedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files/'))
    tempfiles = []

    @classmethod
    def setUpClass(cls):
        """
        Init Haddock server XML-RPC interface
        """

        cls.xmlrpc = HaddockXmlrpcInterface(server_url=settings.haddock_server_url.value,
                                            username=server_username, password=server_password)

    def tearDown(self):
        """
        tearDown method called after each unittest to cleanup
        the files directory
        """

        for tmp in self.tempfiles:
            if os.path.isdir(tmp):
                shutil.rmtree(tmp)
            elif os.path.exists(tmp):
                os.remove(tmp)
            else:
                pass

    def test_xmlrpc_server_methods(self):
        """
        Test if required XML-RPC methods are implemented in Haddock server
        """

        server_methods = [n for n in self.xmlrpc.server.system.listMethods() if not n.startswith('system.')]
        self.assertItemsEqual(server_methods, ['cancelProject', 'checkUser', 'getProjectParams', 'getProjectStatus',
              'getResultsDownloadLocation', 'launchProject', 'listAllProjects', 'listFinishedProjects', 'listUsers'])

    def test_xmlrpc_login(self):
        """
        Test login to the Haddock server
        """

        self.xmlrpc.login()

    def test_xmlrpc_login_failed(self):
        """
        Test login to the Haddock server
        """

        xmlrpc = HaddockXmlrpcInterface(server_url=settings.haddock_server_url.value,
                                        username=server_username, password='faulty_pw')
        self.assertFalse(xmlrpc.login())

    def test_xmlrpc_list_users(self):
        """
        Test 'listUsers' endpoint method. User probably not authorized
        """

        self.assertIsNone(self.xmlrpc.list_users())

    def test_xmlrpc_list_projects(self):
        """
        Test 'listAllProjects' endpoint method. User probably not authorized
        """

        projects = self.xmlrpc.list_projects()

        self.assertIsInstance(projects, list)

    def test_xmlrpc_get_project_status(self):
        """
        Test 'getProjectStatus' endpoint method. Status is either 'done',
        'error' or 'processing'
        """

        for project in self.xmlrpc.list_projects():
            self.assertIn(self.xmlrpc.get_status(project), ('done', 'error', 'processing'))

    def test_xmlrpc_get_result_url(self):
        """
        Test 'getResultsDownloadLocation' endpoint method
        """

        for project in self.xmlrpc.list_projects():
            url = self.xmlrpc.get_results_url(project)
            if url:
                self.assertEqual(url.split('/')[-1], '{0}.tgz'.format(project))

    def test_xmlrpc_get_params(self):
        """
        Test 'getProjectParams' endpoint method.
        Try loading into Graph for the first two projects only
        """

        for project in self.xmlrpc.list_projects()[:2]:
            web = self.xmlrpc.get_params(project)

            webfile = os.path.join(self.filedir, '{0}.web'.format(project))
            with open(webfile, 'w') as wb:
                wb.write(web)
            self.tempfiles.append(webfile)

            model = read_web(web)
            model.node_tools = NodeAxisTools

            self.assertTrue(os.path.isfile(webfile))
            self.assertFalse(model.empty())

    def test_xmlrpc_get_results(self):
        """
        Test download of Haddock project .tgz archive
        """

        for project in self.xmlrpc.list_projects():
            if self.xmlrpc.get_status(project) == 'done':

                dw = self.xmlrpc.get_results(project, self.filedir)
                self.tempfiles.append(dw)
                self.assertTrue(os.path.isdir(dw))

                break

    def test_xmlrpc_load_project(self):
        """
        Test submission of Haddock project as .web parameter file
        """

        project_file = os.path.join(self.filedir, 'easy_run_server_ref.web')
        params = open(project_file, 'r').read()
        project_name = 'xmlrpc_unittest_load'

        response = self.xmlrpc.launch_project(params, project_name)

        self.assertEqual(response, project_name)

        print('Wait 5 seconds to allow server to process submission')
        time.sleep(5)
        self.assertEqual(self.xmlrpc.get_status(project_name), 'processing')
