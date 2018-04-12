from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import numpy as np
import os
import pandas as pd

file_path = os.path.realpath(__file__)
root = os.path.split(file_path)[0]


def create_workdir(name, path="/tmp/pylie"):
    """Create temporal workdir dir"""
    workdir = join(path, name)
    os.makedirs(workdir, exist_ok=True)
    return workdir


def compare_csv_files(file1, file2):
    """check if two csv files are the same"""
    df1 = pd.read_csv(file1).sort_index(axis=1)
    df2 = pd.read_csv(file2).sort_index(axis=1)

    return df1.equals(df2)


def compare_dictionaries(d1, d2):
    """Compare two dictionaries with nested numerical results """
    df1 = pd.DataFrame(d1)
    df2 = pd.DataFrame(d2)

    return df1.equals(df2)


dict_trajectory = {
    "unbound_trajectory": [join(root, "files/trajectory/unbound_trajectory.ene")],
    "bound_trajectory": [join(root, "files/trajectory/bound_trajectory.ene")],
    "lie_vdw_header": "Ligand-Ligenv-vdw",
    "lie_ele_header": "Ligand-Ligenv-ele",
    "workdir": create_workdir("trajectory")}

dict_stable = {"mdframe": join(root, "files/stable/mdframe.csv"),
               "workdir": create_workdir("stable"),
               "minlength": 45}

dict_average = {"mdframe": join(root, "files/average/mdframe_splinefiltered.csv"),
                "workdir": create_workdir("average")}

dict_deltag = {
    "alpha_beta_gamma": [0.5937400744224419,  0.31489794216038647, 0.0],
    "workdir": create_workdir("deltag"),
    "dataframe": join(root, "files/deltag/averaged.csv")}

dict_adan_residue = {
    "workdir": create_workdir("adan_residue_deco"),
    "decompose_files": [join(root, "files/adan_residue_deco/decompose_dataframe.ene")],
    "model_pkl": join(root, "files/adan_residue_deco/params.pkl")}

dict_adan_yrange = {
    "workdir": create_workdir("adan_dene_yrange"),
    "dataframe": join(root, "files/adan_dene_yrange/liedeltag.csv"),
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

expected_adan_yrange_results = {
    'alpha': {0: 0.5937400744224419}, 'beta': {0: 0.3148979421603865}, 'case': {0: 1.0},
    'dg_calc': {0: -24.76012625865582}, 'gamma': {0: 0.0}, 'prob-1': {0: 1.0},
    'w_coul': {0: 8.451392745098037}, 'w_d1': {0: 1.0}, 'w_vdw': {0: -46.18427090196078},
    'ref_affinity': {0: np.NaN}, 'error': {0: np.NaN}, 'CI': {0: 1}}

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
            result_collect = yield self.call(
                "mdgroup.lie_pylie.endpoint.collect_energy_trajectories",
                dict_trajectory)
            assert compare_csv_files(result_collect["mdframe"], dict_stable["mdframe"])
            print("method collect_energy_trajectories succeeded")

            result_average = yield self.call(
                "mdgroup.lie_pylie.endpoint.calculate_lie_average", dict_average)
            assert compare_csv_files(result_average["averaged"], dict_deltag["dataframe"])
            print("method calculate_lie_average succeeded!")

            result_liedeltag = yield self.call(
                "mdgroup.lie_pylie.endpoint.liedeltag", dict_deltag)
            assert compare_csv_files(result_liedeltag["liedeltag_file"], dict_adan_yrange["dataframe"])
            print("method liedeltag succeeded!")

            result_adan_yrange = yield self.call(
                "mdgroup.lie_pylie.endpoint.adan_dene_yrange", dict_adan_yrange)
            assert compare_dictionaries(result_adan_yrange["decomp"], expected_adan_yrange_results)
            print("method adan_dene_yrange succeeded!")

            result_stable = yield self.call(
                "mdgroup.lie_pylie.endpoint.filter_stable_trajectory",
                dict_stable)
            print(result_stable)
            assert compare_csv_files(
                result_stable["output"]["filtered_mdframe"], dict_average["mdframe"])
            print("method filter_stable_trajectory succeeded!")

            # result_adan_dene = yield self.call(
            #     "mdgroup.lie_pylie.endpoint.adan_dene", dict_adan_dene)
            # print(result_adan_dene)

            # result_adan_residues = yield self.call(
            #     "mdgroup.lie_pylie.endpoint.adan_residue_decomp", dict_adan_residue)
            # print(result_adan_residues)


if __name__ == "__main__":
    main(Run_pylie)
