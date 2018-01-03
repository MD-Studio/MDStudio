# -*- coding: utf-8 -*-

import os
import json

def _schema_to_data(schema, data=None, defdict=None):
    
    default_data = defdict or {}
    
    properties = schema.get('properties',{})
    for key,value in properties.items():
        if 'properties' in value:
            default_data[key] = _schema_to_data(value)
        elif 'default' in value:
            default_data[key] = value.get('default')
        else:
            pass
    
    # Update with existing data
    if data:
        default_data.update(data)
    
    return default_data

GROMACS_LIE_SCHEMA = os.path.join(os.path.dirname(__file__), 'gromacs_lie_schema.json')
SETTINGS = _schema_to_data(json.load(open(GROMACS_LIE_SCHEMA)))