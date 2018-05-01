from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import numpy as np
import os
import pybel

file_path = os.path.realpath(__file__)
root = os.path.split(file_path)[0]


def create_workdir(name, path="/tmp/structures"):
    """Create temporal workdir dir"""
    workdir = join(path, name)
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    return workdir


def compare_molecules(mol1, mol2, rtol=1e-5, atol=1e-8):
    """Compare the coordinates of two molecules"""
    m1 = pybel.readfile("mol2", mol1).next()
    m2 = pybel.readfile("mol2", mol2).next()

    arr = np.array([x.coords for x in m1])
    brr = np.array([x.coords for x in m2])

    return np.allclose(arr, brr, rtol, atol)


dict_convert = {
    "output_format": "mol2",
    "workdir": create_workdir("convert"),
    "input_format": "smi",
    "mol": "O1[C@@H](CCC1=O)CCC",
    "from_file": False
}

dict_make3d = {
    "from_file": True,
    "workdir": create_workdir("make3d"),
    "input_format": "mol2",
    "output_format": "mol2",
    "mol": join(root, 'files/structure.mol2')
}

dict_addh = {
    "from_file": True,
    "workdir": create_workdir("addh"),
    "input_format": "mol2",
    "output_format": "mol2",
    "mol": join(root, "files/structure3D.mol2"),
    "pH": 7.4,
    "correctForPH": False
}

dict_info = {
    "mol": join(root, "files/structure3D.mol2"),
    "input_format": "mol2",
}

dict_rotate = {
    "from_file": True,
    "workdir": create_workdir("rotate"),
    "input_format": "mol2",
    "output_format": "mol2",
    "rotations": [
        [1, 0, 0, 90], [1, 0, 0, -90], [0, 1, 0, 90],
        [0, 1, 0, -90], [0, 0, 1, 90], [0, 0, 1, -90]],
    "mol": join(root, "files/structureHs.mol2"),
}

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
            print("toolkits available: {}".format(toolkits['toolkits']))

            convert = yield self.call(
                "mdgroup.lie_structures.endpoint.convert", dict_convert)
            assert compare_molecules(convert['mol'], join(root, 'files/structure.mol2'))
            print("converting {} from smile to mol2 succeeded!".format(
                dict_convert['mol']))

            make3d = yield self.call(
                "mdgroup.lie_structures.endpoint.make3d", dict_make3d)
            assert compare_molecules(make3d['mol'], join(root, 'files/structure3D.mol2'), atol=1e-2)
            print("successful creation of a 3D structure for {}".format(
                dict_convert['mol']))

            addh = yield self.call(
                "mdgroup.lie_structures.endpoint.addh", dict_addh)
            assert compare_molecules(addh['mol'], join(root, 'files/structureHs.mol2'))
            print("added hydrogens sucessfully!")

            info = yield self.call(
                "mdgroup.lie_structures.endpoint.info", dict_info)
            atts = info['attributes']
            assert all((
                atts['formula'] == 'C7H12O2', atts['exactmass'] - 128.083729624 < 1e-5))
            print('attributes information successfully retrieved!')

            rotate = yield self.call(
                "mdgroup.lie_structures.endpoint.rotate", dict_rotate)
            assert compare_molecules(rotate['mol'], join(root, 'files/rotations.mol2'))
            print("rotatation method succeeded!")
            # similarity = yield self.call(
            #     "mdgroup.lie_structures.endpoint.chemical_similarity",
            #     dict_similarity)
            # print(similarity)


if __name__ == "__main__":
    main(Run_structures)
