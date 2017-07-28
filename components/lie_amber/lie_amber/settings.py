# -*- coding: utf-8 -*-

import os

SETTINGS = {
    'amberhome': os.environ.get('AMBERHOME',None),
    'amber_acpype': {
        'charge_method': 'bcc',
        'net_charge': 0,
        'multiplicity': 1,
        'atom_type': 'gaff',
        'engine': 'tleap',
        'outtop': 'all',
        'max_time': 36000,
        'chiral': False,
        'sorted': False,
        'direct': False,
        'disambiguate': False,
        'cnstop': False,
        'gmx45': True,
        'force': False
    },
    'amber_reduce': {
        'flip': False,
        'noflip': True,
        'trim': False,
        'nuclear': False,
        'nooh': False,
        'oh': True,
        'his': False,
        'noheth': False,
        'rotnh3': False,
        'norotnh3': True,
        'rotexist': False,
        'rotexoh': False,
        'allalt': True,
        'onlya': False,
        'charges': False,
        'norotmet': False,
        'noadjust': False,
        'nobuild': False,
        'build': True,
        'keep': False,
        'maxaromdih': 10,
        'nbonds': 3,
        'model': 1,
        'nterm': 1,
        'density': 10,
        'radius': 0,
        'occcutoff': 0.01,
        'h2oocccutoff': 0.66,
        'h2obcutoff': 40,
        'penalty': 1,
        'hbregcutoff': 0.6,
        'hbchargedcut': 0.8,
        'badbumpcut': 0.4,
        'metalbump': 0.865,
        'nonmetalbump': 0.125,
        'segidmap': None,
        'xplor': False,
        'oldpdb': False,
        'bbmodel': False,
        'nocon': False,
        'limit': 600,
        'showscore': False,
        'fix': None,
        'db': None,
        'string': None,
        'quiet': True
    }
}