# -*- coding: utf-8 -*-

from collections import namedtuple
from lie_md.gromacs_topology_amber import correctItp
from os.path import join

import os
import shutil

Files = namedtuple(
    "Files", ("protein", "ligand", "topology"))


def set_gromacs_input(files, gromacs_config, workdir):
    """
    Create input files for gromacs.
    """
    # Input files
    new_files = copy_data_to_workdir(files, workdir)
    gromacs_config['protein_pdb'] = new_files.protein
    gromacs_config['ligand_pdb'] = new_files.ligand
    gromacs_config['ligand_itp'] = new_files.topology

    return fix_topology(
        gromacs_config, workdir, new_files.topology)


def fix_topology(gromacs_config, workdir, topology):
    """
    Adjust topology for the ligand.
    """
    itp_file = join(workdir, 'ligand.itp')
    results = correctItp(
        topology, itp_file, posre=True)

    # Add charges and topology
    gromacs_config['charge'] = results['charge']
    gromacs_config['topology'] = itp_file

    return gromacs_config


def copy_data_to_workdir(files, workdir):
    """
    Move Gromacs related files to the Workdir
    """
    files = Files(*files)

    # Store protein file if available
    protein_file = store_structure_in_file(
        files.protein, workdir, 'protein')

    # Store ligand file if available
    ligand_file = store_structure_in_file(
        files.ligand, workdir, 'ligand')

    # Save ligand topology files
    topology_file = store_structure_in_file(
        files.topology, workdir, 'input_GMX', ext='itp')

    return Files(protein_file, ligand_file, topology_file)


def store_structure_in_file(mol, workdir, name, ext='pdb'):
    """
    Store a molecule in a file if possible.
    """
    file_name = '{}.{}'.format(name, ext)
    dest = join(workdir, file_name)

    if mol is None:
        raise RuntimeError(
            "There is not {} available".format(name))

    elif os.path.isfile(mol):
        shutil.copy(mol, dest)

    elif os.path.isdir(mol):
        path = join(mol, file_name)
        store_structure_in_file(path, workdir, name, ext)

    else:
        with open(dest, 'w') as inp:
            inp.write(mol)

    return dest
