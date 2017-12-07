# -*- coding: utf-8 -*-

"""
package:  lie_structures

LIEStudio small molecule cheminformatics functions

TODO: Include pydpi package?
TODO: Incluce PyBioMed package?
TODO: Include pychem (ChemoPy) package?
TODO: Integrate Cambridge Structural Database, using CSD Python API
TODO: Integrate PaDEL-Descriptor package?
TODO: Integrate PyDescriptor package?
"""

import os

__module__ = 'lie_structures'
__docformat__ = 'restructuredtext'
__version__ = '{major:d}.{minor:d}'.format(major=0, minor=1)
__author__ = 'Marc van Dijk'
__status__ = 'pre-release beta1'
__date__ = '5 august 2016'
__licence__ = 'Apache Software License 2.0'
__url__ = 'https://github.com/NLeSC/LIEStudio'
__copyright__ = "Copyright (c) VU University, Amsterdam"
__rootpath__ = os.path.dirname(__file__)

from .settings import STRUCTURES_SCHEMA as structures_schema
from .settings import settings
from .cheminfo_pkgmanager import CinfonyPackageManager

packages = {'pybel': None,
    'indy': {
        'INDIGO_PATH': '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/bin/indigo-python-1.3.0beta.r16-mac'
    },
    'rdk': {
        'RDKIT_PATH': '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/bin/RDkit'
    },
    'cdk': {
        'JPYPE_JVM': '/System/Library/Frameworks/JavaVM.framework/JavaVM',
        'JVM_LD_LIB': '/System/Library/Frameworks/JavaVM.framework/Libraries',
        'CDK_JAR_PATH': '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/bin/cdk-1.4.15.jar'
    },
    'webel': None,
    'opsin': {
        'JPYPE_JVM': '/System/Library/Frameworks/JavaVM.framework/JavaVM',
        'OPSIN_JAR_PATH': '/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/bin/opsin-1.3.0-jar-with-dependencies.jar'
    },
    'jchem': None,
    'silverwebel': None
}

toolkits = CinfonyPackageManager(packages)