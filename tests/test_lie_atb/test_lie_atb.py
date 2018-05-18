from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import os
import shutil

file_path = os.path.realpath(__file__)
root = os.path.split(file_path)[0]


def create_workdir(name, path="/tmp/mdstudio/lie_atb"):
    """Create temporal workdir dir"""
    workdir = join(path, name)
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    return workdir


def copy_to_workdir(file_path, workdir):
    shutil.copy(file_path, workdir)
    base = os.path.basename(file_path)
    return join(workdir, base)


workdir = create_workdir("lie_atb")
path_mol = copy_to_workdir(
    join(root, "files/structure.mol2"), workdir)

dict_query = {
    "netcharge": 0,
    "dim": 3,
    "exactmass": 128.083729624,
    "title": "ligand",
    "PartialCharges": "GASTEIGER",
    "energy": 0.0,
    "molwt": 128.16898000000003,
    "structure_format": "mol2",
    "mol": path_mol,
    "formula": "C7H12O2",
    "isfile": True,
    "workdir": workdir
}


class Run_atb(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):

            result_collect = yield self.call(
                "mdgroup.lie_atb.endpoint.structure_query",
                dict_query)
        print(result_collect)


if __name__ == "__main__":
    main(Run_atb)
