# -*- coding: utf-8 -*-

"""
file: gromacs_gromit.py

Prepaire gromit command line input
"""

GROMIT_ARG_DICT = {
    'forcefield': '-ff',
    'charge': '-charge',
    'gromacs_lie': '-lie',
    'periodic_distance': '-d',
    'temperature': '-t',
    'prfc': '-prfc',
    'ttau': '-ttau',
    'salinity': '-conc',
    'solvent': '-solvent',
    'ptau': '-ptau',
    'sim_time': '-time',
    'gromacs_vsite': '-vsite',
    'gmxrc': '-gmxrc',
    'gromacs_rtc': '-rtc',
    'gromacs_ndlp': '-ndlp'}


def gromit_cmd(options):

    gmxRun = './gmx45md.sh '
    for arg, val in options.items():
        if arg in GROMIT_ARG_DICT:
            if val == True:
                gmxRun += '{0} '.format(GROMIT_ARG_DICT[arg])
            elif val:
                gmxRun += '{0} {1} '.format(GROMIT_ARG_DICT[arg], val)
            else:
                pass

    return gmxRun
