# -*- coding: utf-8 -*-

from lie_plants_docking.plants_docking import PlantsDocking
from lie_plants_docking.utils import prepaire_work_dir
from mdstudio.component.session import ComponentSession
from mdstudio.api.endpoint import endpoint


class DockingWampApi(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @endpoint('docking', 'docking_request', 'docking_response')
    def run_docking(self, request, claims):
        """
        Perform a PLANTS (Protein-Ligand ANT System) molecular docking.
        For a detail description of the input see the file:
        schemas/endpoints/docking-request.v1.json
        """
        task_id = self.component_config.session.session_id
        self.log.info("Plants Docking ID: ", task_id)

        # Docking options are equal to the request but for the workdir
        plants_config = request.copy()
        plants_config.pop('workdir')

        # Prepaire docking directory
        plants_workdir = prepaire_work_dir(request['workdir'], create=True)

        # Run docking
        docking = PlantsDocking(plants_workdir, plants_config)
        success = docking.run(
            plants_config['protein_file'], plants_config['ligand_file'])

        if success:
            status = 'completed'
            output = docking.results()
        else:
            self.log.error('PLANTS docking FAILS!!')
            docking.delete()
            status = 'failed'
            output = None

        return {'status': status, 'output': output}
