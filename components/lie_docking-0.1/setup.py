#! /usr/bin/env python
# -*- coding: utf-8 -*-

# package: lie_docking
# file: setup.py
#
# Part of ‘lie_docking’, a package providing molecular docking functionality
# for the LIEStudio package.
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

distribution_name = 'lie_docking'
main_module = __import__(distribution_name)
main_module_doc = main_module.__doc__

setup(
    name=distribution_name,
    version=main_module.__version__,
    description='LIEStudio molecular docking module',
    author='Marc van Dijk, VU University, Amsterdam, The Netherlands',
    author_email='m4.van.dijk@vu.nl',
    url=main_module.__url__,
    license=main_module.__licence__,
    keywords='LIEStudio molecular docking',
    long_description=main_module_doc,
    platforms=['Any'],
    packages=find_packages(),
    py_modules=[distribution_name],
    install_requires=['twisted','autobahn', 'scipy'],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'autobahn.twisted.wamplet': [
            'wamp_services = lie_docking.wamp_services:make'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        ],
)