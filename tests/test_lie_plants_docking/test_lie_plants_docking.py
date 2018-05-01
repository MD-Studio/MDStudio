from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil

workdir = "/tmp/plants_docking"
protein_file = os.path.join(os.getcwd(), "DT_conf_1.mol2")
ligand_file = os.path.join(os.getcwd(), "ligand.mol2")
exec_path = os.path.abspath("../../bin/plants_linux")
if os.path.exists(workdir):
    shutil.rmtree(workdir)


class Run_docking(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            self.call(
                "mdgroup.lie_plants_docking.endpoint.docking",
                {"protein_file": protein_file,
                 "ligand_file": ligand_file,
                 "min_rmsd_tolerance": 3.0,
                 "cluster_structures": 100,
                 "bindingsite_radius": 12.0,
                 "bindingsite_center": [
                     4.926394772324452, 19.079624537618873, 21.98915631296689],
                 "workdir": workdir,
                 "exec_path": exec_path})


if __name__ == "__main__":
    main(Run_docking)
