# -*- coding: utf-8 -*-

"""
file: model_user.py

Graph model classes for dealing with user information
"""

import getpass

from lie_graph.graph_mixin import NodeEdgeToolsBaseClass


class User(NodeEdgeToolsBaseClass):

    def username(self):
        """
        Get user name of current system user
        """

        return getpass.getuser()
