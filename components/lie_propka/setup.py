# -*- coding: utf-8 -*-

# package: lie_propka
# file: setup.py
#
# Part of ‘lie_propka’, a package providing an interface to the PROPKA
# software suite for prediction of the pKa values of ionizable groups in
# proteins and protein-ligand complexes based in the 3D structure.
# http://propka.org
#
# Copyright © 2017 Marc van Dijk, VU University Amsterdam, the Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

distribution_name = 'lie_propka'
test_requirements = ['unittest2']

setup(
    name=distribution_name,
    version=0.1,
    description='LIEStudio component providing an interface to the PropKa software suite',
    author='Marc van Dijk, VU University, Amsterdam, The Netherlands',
    author_email='m4.van.dijk@vu.nl',
    url='https://github.com/MD-Studio/MDStudio',
    license='Apache Software License 2.0',
    keywords='LIEStudio PropKa pKa',
    platforms=['Any'],
    packages=find_packages(),
    package_data={'': ['*.json']},
    py_modules=[distribution_name],
    include_package_data=True,
    install_requires=['jsonschema', 'pandas', 'propkatraj'] + test_requirements,
    zip_safe=True,
    entry_points={
        'autobahn.twisted.wamplet': [
            'wamp_services = lie_propka.wamp_services:make'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
    ],
)
