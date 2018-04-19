from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import os


def create_workdir(name, path="/tmp/structures"):
    """Create temporal workdir dir"""
    workdir = join(path, name)
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    return workdir


dict_similarity = {
    "mol_format": "smi",
    "ci_cutoff": 0.3617021276595745,
    "workdir": create_workdir('similarity'),
    "test_set": ["O1[C@@H](CCC1=O)CCC"],
    "reference_set": [
      "c1(c(cccc1Nc1c(cccc1)C(=O)O)C)C",
      "c12ccccc1nc1c(c2N)CCCC1",
      "c1ccc(c(c1)[N+](=O)[O-])[C@H]1C(=C(NC(=C1C(=O)OC)C)C)C(=O)OC",
      "c1cc(ccc1OCC)NC(=O)C",
      "c12c3c(ccc1c(=O)cc(o2)c1ccccc1)cccc3",
      "c1cc(cc(c1N/C=N/O)C)CCCC",
      "c1(cccnc1Nc1cc(ccc1)C(F)(F)F)C(=O)O",
      "c1ccc(c(c1C)OC[C@H](C)N)C",
      "c1(OC[C@H](CNC(C)C)O)c2c(ccc1)cccc2",
      "c12ccccc1cccc2",
      "c12ccccc1cccc2C",
      "c12ccccc1ccc(c2)C",
      "c12ccccc1ccc(c2)F",
      "c12ccccc1cc(cc2C)C",
      "c12ccccc1c(ccc2C)C",
      "c12cccc(c1cccc2Cl)Cl",
      "c12cc(ccc1cc(cc2)C)C",
      "C1CCC(=O)OCC1",
      "O1[C@@H](CCC1=O)C",
      "O1[C@@H](CCC1=O)CC",
      "O1[C@@H](CCC1=O)CCC",
      "O1[C@@H](CCC1=O)CCCCC",
      "O1[C@@H](CCC1=O)CCCCCC",
      "O1[C@@H](CCC1=O)CCCCCCC",
      "C1C[C@@H](OC(=O)C1)CCCCC",
      "c1c2c(ccc1)OC(=O)C2",
      "c1c2c(ccc1)CC(=O)C2",
      "c1c2c(ccc1)OCC2",
      "c1c2c(ccc1)oc(=O)[nH]2",
      "c1(ccccc1)c1ccccc1",
      "c1c(cccc1)c1ccc(cc1)Cl",
      "C1CCCC(C1)CCCC",
      "[C@@H]1(OC(=O)CC1)c1ccccc1",
      "c1(cc(oc(=O)c1)C)C",
      "C1CC(=O)N([C@H]1c1cccnc1)C"
    ]
}


class Run_structures(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            toolkits = yield self.call(
                "mdgroup.lie_structures.endpoint.supported_toolkits",
                {})
            assert "pybel" in toolkits["toolkits"]
            print("toolkits available!")

            similarity = yield self.call(
                "mdgroup.lie_structures.endpoint.chemical_similarity",
                dict_similarity)
            print(similarity)


if __name__ == "__main__":
    main(Run_structures)
