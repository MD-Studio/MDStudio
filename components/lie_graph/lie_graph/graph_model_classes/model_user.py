# -*- coding: utf-8 -*-

"""
file: model_user.py

Graph model classes for dealing with user information
"""

import getpass

from lie_graph.graph_mixin import NodeEdgeToolsBaseClass


class User(NodeEdgeToolsBaseClass):

    @staticmethod
    def username():
        """
        Get user name of current system user
        """

        return getpass.getuser()

    def set(self, key=None, value=None):
        """
        Set to current system user if called without arguments.
        """

        key = key or self.node_value_tag
        if key == self.node_value_tag and not value:
            value = self.username()

        self.nodes[self.nid][key] = value
