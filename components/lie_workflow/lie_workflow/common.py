# -*- coding: utf-8 -*-

import logging


def _schema_to_data(schema, data=None, defdict=None):

    default_data = defdict or {}

    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for key, value in properties.items():
        if key in required:
            if 'properties' in value:
                default_data[key] = _schema_to_data(value)
            else:
                default_data[key] = value.get('default')

    # Update with existing data
    if data:
        default_data.update(data)

    return default_data


class WorkflowError(Exception):

    def __init__(self, message):

        super(WorkflowError, self).__init__(message)

        logging.error(message)
