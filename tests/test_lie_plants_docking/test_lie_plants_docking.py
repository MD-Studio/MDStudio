from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil


def copy_to_workdir(file_path, workdir):
    shutil.copy(file_path, workdir)
    base = os.path.basename(file_path)
    return os.path.join(workdir, base)


workdir = "/tmp/mdstudio/lie_plants_docking"
protein_file = copy_to_workdir(
    os.path.join(os.getcwd(), "DT_conf_1.mol2"), workdir)
ligand_file = copy_to_workdir(
    os.path.join(os.getcwd(), "ligand.mol2"), workdir)
exec_path = copy_to_workdir("plants_linux", workdir)


class Run_docking(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            result = yield self.call(
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
            assert result['status'] == 'completed'


if __name__ == "__main__":
    main(Run_docking)
