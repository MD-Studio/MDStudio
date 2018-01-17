# -*- coding: utf-8 -*-

"""
LIEStudio propka component

PROPKA predicts the pKa values of ionizable groups in proteins and
protein-ligand complexes based in the 3D structure.

When using this component in scientific work please cite:
- Mats H.M. Olsson, Chresten R. Sondergard, Michal Rostkowski, and Jan H. Jensen
  "PROPKA3: Consistent Treatment of Internal and Surface Residues in Empirical
  pKa predictions." Journal of Chemical Theory and Computation, 7(2):525-537
  (2011)
"""

import os
import json

__module__ = 'lie_propka'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '5 august 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/MD-Studio/MDStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)
__all__ = ['RunPropka']


def _schema_to_data(schema, data=None, defdict=None):
    default_data = defdict or {}

    properties = schema.get('properties', {})

    for key, value in properties.items():
        if 'default' in value:
            if 'properties' in value:
                default_data[key] = _schema_to_data(value)
            else:
                default_data[key] = value.get('default')
        else:
            default_data[key] = None

    # Update with existing data
    if data:
        default_data.update(data)

    return default_data


propka_schema = json.load(open(os.path.join(__rootpath__, 'propka_schema.json')))
settings = _schema_to_data(propka_schema)

from wamp_services import RunPropka