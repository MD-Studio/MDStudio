# -*- coding: utf-8 -*-

import json
import os
import pkgutil
import shutil
import tempfile
from lie_amber.wamp_services import get_amber_config
from lie_amber.ambertools import amber_acpype
from .util_test import (remove_workdir, schema_to_data)


ACPYPE_LIE_SCHEMA = os.path.join(
    pkgutil.get_data(
        'lie_amber', 'schemas/endpoints/acpype-request.v1.json'))

settings_acpype = get_amber_config(
    schema_to_data(json.loads(ACPYPE_LIE_SCHEMA)))


@remove_workdir
def test_amber_acepype():
    path = os.path.join(os.path.dirname(__file__), 'files/input.mol2')
    workdir = tempfile.mkdtemp('tmp', dir='.')
    shutil.copy(path, workdir)
    output = amber_acpype(path, settings_acpype, workdir)
    assert os.path.isdir(output['path'])


def test_amber_reduce():
    pass
