# -*- coding: utf-8 -*-

"""
file: graph_mixin.py

NodeTools and EdgeTools classes for axis based graphs (GraphAxis class)
"""

from lie_graph.graph_mixin import NodeTools, EdgeTools


class NodeAxisTools(NodeTools):

    def __iter__(self):

        for child in self.graph.children():
            yield child


class EdgeAxisTools(EdgeTools):

    def __iter__(self):
        pass

