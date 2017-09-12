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
    'solvent', '-solvent',
    'ptau': '-ptau',
    'sim_time': '-time',
    'gromacs_vsite': '-vsite',
    'gmxrc': '-gmxrc'}

def gromit_cmd(options):
    
    gmxRun = './gmx45md.sh '
    for arg,val in options.items():
        if arg in GROMIT_ARG_DICT:        
            if val == True:
                gmxRun += '{0} '.format(GROMIT_ARG_DICT[arg])
            else:
                gmxRun += '{0} {1} '.format(GROMIT_ARG_DICT[arg],val)
    
    return gmxRun
