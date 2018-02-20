from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os

cerise_file = "cerise_config_gt.json"
ligand_file = "compound.pdb"
protein_file = None
protein_top = "protein.top"
topology_file = "input_GMX.itp"
include = ["attype.itp", "ref_conf_1-posre.itp"]
residues = [28, 29, 65, 73, 74]
workdir = "mdstudio_test"
if not os.path.exists(workdir):
    os.mkdir(workdir)


class Run_test(ComponentSession):

    def on_run(self):
        with self.group_context('mdgroup'):
            self.call(
                "mdgroup.liemd.endpoint.liemd",
                {"cerise_file": cerise_file,
                 "ligand_file": ligand_file,
                 "protein_file": None,
                 "protein_top": protein_top,
                 "topology_file": topology_file,
                 "include": include,
                 "residues": residues,
                 "workdir": workdir})


if __name__ == "__main__":
    main(Run_test)
