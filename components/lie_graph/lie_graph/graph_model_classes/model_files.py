# -*- coding: utf-8 -*-

"""
file: model_files.py

Graph model classes for working with files
"""

import os
import logging

from lie_graph.graph_mixin import NodeEdgeToolsBaseClass


class FilePath(NodeEdgeToolsBaseClass):

    @property
    def exists(self):

        path = self.get()
        if path:
            return os.path.exists(path)
        return False

    @property
    def iswritable(self):

        return os.access(self.get(), os.W_OK)

    def set(self, key, value=None, absolute=True):

        if key == self.node_value_tag and absolute:
            value = os.path.abspath(value)

        self.nodes[self.nid][key] = value

    def create_dirs(self):
        """
        Create directories of the stored path

        :return:        Absolute path to working directory
        :rtype:         :py:str
        """

        path = self.get()
        if self.exists and self.iswritable:
            logging.info('Directory exists and writable: {0}'.format(path))
            return path

        try:
            os.makedirs(path, 0755)
        except Exception:
            logging.error('Unable to create project directory: {0}'.format(path))

        return path
