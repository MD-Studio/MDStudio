#! /usr/bin/env python
# -*- coding: utf-8 -*-

# package: lie_db
# file: setup.py
#
# Part of ‘lie_db’, a package providing MongoDB access for the MDStudio
# package.
#
# Copyright © 2016 Marc van Dijk, VU University Amsterdam, the Netherlands
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


def pipenv_requires():
    from pipenv.project import Project
    from pipenv.utils import convert_deps_to_pip

    pfile = Project(chdir=True).parsed_pipfile
    return convert_deps_to_pip(pfile['packages'], r=False)


distribution_name = 'lie_db'
setup(
    name=distribution_name,
    version='1.0.0',
    license='Apache Software License 2.0',
    description='PyMongo database drivers for the MDStudio application',
    author='Marc van Dijk - VU University - Amsterdam,' \
           'Paul Visscher - Zefiros Software (www.zefiros.eu),' \
           'Felipe Zapata - eScience Center (https://www.esciencecenter.nl/)',
    author_email='m4.van.dijk@vu.nl, contact@zefiros.eu',
    url='https://github.com/MD-Studio/MDStudio',
    keywords='MongoDB PyMongo MDStudio database',
    platforms=['Any'],
    packages=find_packages(),
    py_modules=[distribution_name],
    install_requires=pipenv_requires(),
    test_suite="tests",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Database',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
    ],
)
