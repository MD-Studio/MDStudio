from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import os

residues = [28, 29, 65, 73, 74]
workdir = "/app/scripts/simple_test/mdstudio_test"
if not os.path.exists(workdir):
    os.mkdir(workdir)

cerise_file = join(workdir, "cerise_config_gt.json")
ligand_file = join(workdir, "compound.pdb")
protein_file = None
protein_top = join(workdir, "protein.top")
topology_file = join(workdir, "input_GMX.itp")
include = [join(workdir, "attype.itp"), join(workdir, "ref_conf_1-posre.itp")]
amber_input = "input.mol2"


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

    # def on_run(self):
    #     with self.group_context('mdgroup'):
    #         self.call(
    #             "mdgroup.lie_amber.endpoint.acpype",
    #             {"structure": amber_input,
    #              "workdir": workdir})


if __name__ == "__main__":
    main(Run_test)
