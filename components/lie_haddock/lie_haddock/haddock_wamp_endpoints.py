# -*- coding: utf-8 -*-

from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession

from lie_graph.graph_io.io_dict_format import write_dict
from lie_graph.graph_io.io_web_format import write_web

from haddock_helper_methods import resolve_credentials
from haddock_xmlrpc_endpoints import HaddockXmlrpcInterface
from haddock_model import (load_project, save_project, new_project, remove_haddock_data_block, new_parameter_block,
                           edit_parameter_block)


class HaddockComponent(ComponentSession):

    def authorize_request(self, uri, claims):
        """
        Authorize request

        If you were allowed to call this in the first place,
        I will assume you are authorized
        """

        return True

    @endpoint('new_project', 'haddock-project-request', 'haddock-project-request')
    def new_project(self, request, claims):
        """
        Create a new default Haddock project.

        Base project template is defined by 'haddock-project-request' JSON Schema.
        Request and response are the same.
        """

        project_id = request['project_id']

        # Create new base project
        project = new_project(project_id)

        # Update project parameters and save
        params = edit_parameter_block(project, 'project', request)
        save_project(project, request['project_id'])

        # Return parameters as dictionary
        result = {'project_id': project_id}
        result.update(write_dict(params, allow_none=False))
        return result

    @endpoint('import_project', 'haddock-project-import-request', 'haddock-project-import-response')
    def import_project(self, request, claims):

        pass

    @endpoint('export_project', 'haddock-project-export-request', 'haddock-project-export-response')
    def export_project(self, request, claims):

        pass

    @endpoint('remove_project_data', 'haddock-remove-request', 'haddock-remove-response')
    def remove_project_data(self, request, claims):
        """
        Remove a single parameter or parameter block from a Haddock project.
        """

        success = False
        project = load_project(request['project_id'])
        if not project.empty():
            success = remove_haddock_data_block(project, request.get('block_id'),
                                                multiple=request.get('multiple', False))

            # Update project
            if success:
                save_project(project, request['project_id'])

        return {'project_id': request['project_id'], 'success': success}

    @endpoint('edit_dani', 'haddock-dani-request', 'haddock-dani-request')
    def edit_dani(self, request, claims):
        """
        Create new or edit existing Haddock Relaxation anisotropy restraints
        (DANI)
        """

        project = load_project(request['project_id'])
        result = {}
        if not project.empty():

            block_id = request.get('block_id')

            if request['new']:
                block_id, params = new_parameter_block(project, 'haddock-dani-request.v1', 'DANIParameters', max_mult=5)

            params = edit_parameter_block(project, block_id, request)
            save_project(project, request['project_id'])

            result = {'project_id': request['project_id']}
            result.update(write_dict(params, allow_none=False))

        return result

    @endpoint('edit_rdc', 'haddock-rdc-request', 'haddock-rdc-request')
    def edit_rdc(self, request, claims):
        """
        Create new or edit existing Haddock Residual Dipolar Coupling
        definition (RDC)
        """

        project = load_project(request['project_id'])
        result = {}
        if not project.empty():

            block_id = request.get('block_id')

            if request['new']:
                block_id, params = new_parameter_block(project, 'haddock-rdc-request.v1', 'RDCParameters', max_mult=5)

            params = edit_parameter_block(project, block_id, request)
            save_project(project, request['project_id'])

            result = {'project_id': request['project_id']}
            result.update(write_dict(params, allow_none=False))

        return result

    @endpoint('edit_pcs', 'haddock-pcs-request', 'haddock-pcs-request')
    def edit_pcs(self, request, claims):
        """
        Create new or edit existing Haddock Pseudo Contact Shift (PCS)
        """

        project = load_project(request['project_id'])
        result = {}
        if not project.empty():

            block_id = request.get('block_id')

            if request['new']:
                block_id, params = new_parameter_block(project, 'haddock-pcs-request.v1', 'PCSParameters', max_mult=10)

            params = edit_parameter_block(project, block_id, request)
            save_project(project, request['project_id'])

            result = {'project_id': request['project_id']}
            result.update(write_dict(params, allow_none=False))

        return result

    @endpoint('edit_karplus', 'haddock-karplus-request', 'haddock-karplus-request')
    def edit_karplus(self, request, claims):
        """
        Create new or edit existing Haddock Karplus Constant definition
        """

        project = load_project(request['project_id'])
        result = {}
        if not project.empty():

            block_id = request.get('block_id')

            if request['new']:
                block_id, params = new_parameter_block(project, 'haddock-karplus-request.v1', 'KarplusConstants',
                                                       max_mult=5)

            params = edit_parameter_block(project, block_id, request)
            save_project(project, request['project_id'])

            result = {'project_id': request['project_id']}
            result.update(write_dict(params, allow_none=False))

        return result

    @endpoint('edit_partner', 'haddock-partner-request', 'haddock-partner-request')
    def edit_partner(self, request, claims):
        """
        Create new or edit existing Haddock molecular partner
        """

        project = load_project(request['project_id'])
        result = {}
        if not project.empty():

            block_id = request.get('block_id')

            if request['new']:
                block_id, params = new_parameter_block(project, 'haddock-partner-request.v1', 'HaddockPartnerParameters',
                                                       max_mult=5)

            params = edit_parameter_block(project, block_id, request)
            save_project(project, request['project_id'])

            result = {'project_id': request['project_id']}
            result.update(write_dict(params, allow_none=False))

        return result

    @endpoint('list_projects', 'haddock-list-projects-request', 'haddock-list-projects-response')
    def list_projects(self, request, claims):
        """
        List user projects and their
        """

        # Get username and password
        username, password = resolve_credentials(self.component_config.settings)

        # Get projects
        xmlrpc = HaddockXmlrpcInterface(server_url=self.component_config.settings['haddock_server_url'],
                                        username=username, password=password)

        # Get projects from Haddock server
        projects = set(xmlrpc.list_projects())

        # If not all but a specific set of projects is requested, check if they
        # are available
        request_specific_projects = set(request.get('projects', []))
        if len(request_specific_projects):
            diff = request_specific_projects.difference(projects)
            if diff:
                self.log.warning('Following projects not available at server: {0}'.format(diff))
            projects = request_specific_projects.intersection(projects)

        # Get project status from Haddock server
        result = {}
        for project in projects:
            result[project] = xmlrpc.get_status(project)

        return result

    @endpoint('submit_project', 'haddock-submit-project-request', 'haddock-submit-project-response')
    def submit_project(self, request, claims):
        """
        Submit a Haddock project to the Haddock server
        """

        project = load_project(request['project_id'])
        result = {'project_id': None}
        if not project.empty():

            webformat = write_web(project)
            response = self.xmlrpc.launch_project(webformat, request['project_id'])
            result['project_id'] = response

            if response != request['project_id']:
                self.loger.error('Unable to submit project {0} to Haddock server'.format(request['project_id']))
        else:
            self.log.error('Unable to load project {0}'.format(request['project_id']))

        return result
