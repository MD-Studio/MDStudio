# -*- coding: utf-8 -*-

"""
file: cheminfo_pkgmanager.py

Manage import of Cinfony supported cheminformatics software
"""

import os
import sys
import collections
import importlib
import logging


class CinfonyPackageManager(collections.MutableMapping):

    def __init__(self, packages, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

        for package, settings in packages.items():
            pkg_handler = getattr(self, 'set_{0}'.format(package), None)
            if pkg_handler:
                pkg_handler(settings)
            self._import_pkg(package)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def _import_pkg(self, package):

        try:
            self[package] = importlib.import_module(
                "cinfony.{0}".format(package))
        except:
            msg = 'Unable to import cheminformatics package {0} using cinfony'
            logging.debug(msg.format(package))

    def set_cdk(self, settings):

        # Init JPype JAVA HOME
        jvm = settings['JPYPE_JVM']
        if jvm not in os.environ:
            os.environ['JPYPE_JVM'] = jvm

        # Set LD_LIBRARY_PATH
        ldlibpath = os.environ.get('LD_LIBRARY_PATH', '').split(':')
        ldl = settings['JVM_LD_LIB']
        if ldl not in ldlibpath:
            ldlibpath.append(ldl)
        os.environ['LD_LIBRARY_PATH'] = ':'.join(ldlibpath)

        # Set path to CDK
        class_path = os.environ.get('CLASSPATH', '').split(':')
        if settings['CDK_JAR_PATH'] not in class_path:
            class_path.append(settings['CDK_JAR_PATH'])
        os.environ['CLASSPATH'] = ':'.join(class_path)

    def set_opsin(self, settings):

        # Init JPype JAVA HOME
        jvm = settings['JPYPE_JVM']
        if jvm not in os.environ:
            os.environ['JPYPE_JVM'] = jvm

        # Set path to OPSIN
        class_path = os.environ.get('CLASSPATH', '').split(':')
        if settings['OPSIN_JAR_PATH'] not in class_path:
            class_path.append(settings['OPSIN_JAR_PATH'])
        os.environ['CLASSPATH'] = ':'.join(class_path)

    def set_indy(self, settings):

        # Set path to Indigo
        if settings['INDIGO_PATH'] not in sys.path:
            sys.path.append(settings['INDIGO_PATH'])

    def set_rdk(self, settings):

        # Set path to RDKit
        rdbase = settings['RDKIT_PATH']
        if 'RDBASE' not in os.environ:
            os.environ['RDBASE'] = rdbase

        # Set DYLD_LIBRARY_PATH
        ldlibpath = os.environ.get('DYLD_LIBRARY_PATH', '').split(':')
        ldl = os.path.join(rdbase, 'lib')
        if ldl not in ldlibpath:
            ldlibpath.append(ldl)
        os.environ['DYLD_LIBRARY_PATH'] = ':'.join(ldlibpath)

        if rdbase not in sys.path:
            sys.path.append(rdbase)