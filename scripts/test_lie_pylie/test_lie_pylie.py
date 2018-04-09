from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import numpy as np
import os
import pandas as pd


def create_workdir(name, path="/tmp/pylie"):
    """Create temporal workdir dir"""
    workdir = join(path, name)
    os.makedirs(path, exists_ok=True)
    return workdir


def compare_csv_files(file1, file2):
    """check if two csv files are the same"""
    x = pd.read_csv(file1)
    y = pd.read_csv(file1)

    return x == y


dict_trajectory = {
    "unbound_trajectory": [join("files/trajectory/unbound_trajectory.ene")],
    "bound_trajectory": [join("files/trajectory/bound_trajectory.ene")],
    "lie_vdw_header": "Ligand-Ligenv-vdw",
    "lie_ele_header": "Ligand-Ligenv-ele",
    "decomp_files": [join("files/trajectory/bound_trajectory.ene")],
    "workdir": create_workdir("trajectory")}

dict_stable = {"mdframe": join("files/stable/mdframe.csv"),
               "workdir": create_workdir("stable")}

dict_average = {"mdframe": join("files/stable/mdframe_splinefiltered.csv"),
                "workdir": create_workdir("average")}

dict_deltag = {
    "alpha": 0.5937400744224419,
    "beta": 0.31489794216038647,
    "workdir": create_workdir("deltag"),
    "dataframe": "averaged.csv",
    "gamma": 0.0}

dict_similarity = {
    "mol_format": "smi",
    "ci_cutoff": 0.3617021276595745,
    "workdir": create_workdir("similarity"),
    "test_set": [
        "O1[C@@H](CCC1=O)CCC"],
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
        "C1CC(=O)N([C@H]1c1cccnc1)C"]}

dict_adan_residue = {
    "workdir": create_workdir("adan_residue_deco"),
    "bound_trajectory": dict_trajectory["bound_trajectory"],
    "unbound_trajectory": dict_trajectory["unbound_trajectory"],
    "decomp_files": dict_trajectory["decomp_files"],
    "model_pkl": "files/adan_residue_deco/params.pkl"}

dict_adan_yrange = {
    "workdir": create_workdir("adan_dene_yrange"),
    "dataframe": "files/adan_dene_yrange/liedeltag.csv",
    "ymin": -42.59,
    "ymax": -10.79,
    "liedeltag": {
          "case": {
            "0": 1.0
          },
          "prob-1": {
            "0": 1.0
          },
          "w_d1": {
            "0": 1.0
          },
          "w_coul": {
            "0": 8.451392745098037
          },
          "ref_affinity": {
            "0": np.NaN
          },
          "dg_calc": {
            "0": -24.76012625865582
          },
          "beta": {
            "0": 0.31489794216038647
          },
          "w_vdw": {
            "0": -46.18427090196078
          },
          "error": {
            "0": np.NaN
          },
          "alpha": {
            "0": 0.5937400744224419
          },
          "gamma": {
            "0": 0.0
          }
        }
}

dict_adan_dene = {
    "ci_cutoff": 13.690708685318436,
    "workdir": create_workdir("dict_adan_dene"),
    "liedeltag": dict_adan_yrange["liedeltag"],
    "model_pkl": dict_adan_residue["model_pkl"],
    "dataframe": dict_adan_yrange["dataframe"],
    "center": [-53.11058012546337, 21.656883661248937]}


class Run_pylie(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            result_collect = self.call(
                "mdgroup.lie_pylie.endpoint.collect_energy_trajectories",
                dict_trajectory)
            assert compare_csv_files(result_collect["mdframe"], dict_stable["mdframe"])

            # result_stable = self.call(
            #     "mdgroup.lie_pylie.endpoint.filter_stable_trajectory",
            #     dict_stable)

            # result_average = self.call(
            #     "mdgroup.lie_pylie.endpoint.calculate_lie_average", dict_average)

            # result_liedeltag = self.call(
            #     "mdgroup.lie_pylie.endpoint.liedeltag", dict_deltag)

            # result_similarity = self.call(
            #     "mdgroup.lie_pylie.endpoint.chemical_similarity", dict_similarity)

            # result_adan_residues = self.call(
            #     "mdgroup.lie_pylie.endpoint.adan_residue_decomp", dict_adan_residue)

            # result_adan_yrange = self.call(
            #     "mdgroup.lie_pylie.endpoint.adan_dene_yrange", dict_adan_yrange)

            # result_adan_dene = self.call(
            #     "mdgroup.lie_pylie.endpoint.adan_dene", dict_adan_dene)


if __name__ == "__main__":
    main(Run_pylie)
