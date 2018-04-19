# -*- coding: utf-8 -*-

"""
file: model_identifiers.py

Graph model classes for working (unique) identifiers
"""

import re
import uuid

from lie_graph.graph_mixin import NodeEdgeToolsBaseClass
from lie_graph.graph_helpers import GraphValidationError

UUID_REGEX = re.compile(r'^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$')


class UUID(NodeEdgeToolsBaseClass):

    @staticmethod
    def create():

        return str(uuid.uuid1())

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if isinstance(value, (str, unicode)) and UUID_REGEX.match(value):
                pass
            else:
                raise GraphValidationError('No valid UUID: {0}'.format(value), self)

        self.nodes[self.nid][key] = value
