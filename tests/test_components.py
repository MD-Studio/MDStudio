from os.path import join
from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os

# Workdirs
cwd = os.getcwd()
workdir = "/tmp/mdstudio"

# lie_amber files
structure_path = join(cwd, "files/lie_amber/input.mol2")
with open(structure_path, 'r') as f:
    amber_input = f.read()

# lie_pylie files
root = "/home/mdstudio/lie_pylie/tests/wamp_test"
dict_trajectory = {
    "unbound_trajectory": [join(root, "files/trajectory/unbound_trajectory.ene")],
    "bound_trajectory": [join(root, "files/trajectory/bound_trajectory.ene")],
    "lie_vdw_header": "Ligand-Ligenv-vdw",
    "lie_ele_header": "Ligand-Ligenv-ele",
    "workdir": join(workdir, "lie_pylie/trajectory")}


class Run_components(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        # test_amber
        result = yield self.call(
            "mdgroup.lie_amber.endpoint.acpype",
            {"structure": amber_input,
             "workdir": join(workdir, 'lie_amber')})
        assert os.path.isfile(result['gmx_top'])
        print("LIE Amber up and running!")

        # test lie_structures
        toolkits = yield self.call(
            "mdgroup.lie_structures.endpoint.supported_toolkits",
            {})
        assert "pybel" in toolkits["toolkits"]
        print("LIE structure up and running!")


if __name__ == "__main__":
    main(Run_components)
