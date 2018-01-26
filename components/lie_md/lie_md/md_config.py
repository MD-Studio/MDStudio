# -*- coding: utf-8 -*-

from lie_md.gromacs_topology_amber import (correctItp, fix_atom_types_file)
from os.path import join
from twisted.logger import Logger

logger = Logger()


def set_gromacs_input(gromacs_config, workdir, dict_input):
    """
    Create input files for gromacs.
    """
    # update input
    gromacs_config.update(dict_input)

    # added a job type
    job_type = "solvent_ligand_md" if gromacs_config['protein_file'] is None else "protein_ligand_md"
    gromacs_config['job_type'] = job_type

    # correct topology
    return fix_topology_ligand(gromacs_config, workdir)


def fix_topology_ligand(gromacs_config, workdir):
    """
    Adjust topology for the ligand.
    """
    itp_file = join(workdir, 'ligand.itp')
    dict_results = correctItp(
        gromacs_config['topology_file'], itp_file,  posre=True)

    # Add charges and topology
    gromacs_config['charge'] = dict_results['charge']
    gromacs_config['topology_file'] = dict_results['itp_filename']

    # correct atomtypes file
    fix_atom_types_file(
        gromacs_config['include'], dict_results['attypes'], workdir)

    # Added further include file
    include_itp = dict_results.get('posre_filename', None)
    if include_itp is not None:
        gromacs_config['include'].append(include_itp)

    return gromacs_config
