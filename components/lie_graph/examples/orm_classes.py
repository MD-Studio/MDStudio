# -*- coding: utf-8 -*-

from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools


class Segid(NodeAxisTools):

    def custom_print(self):

        return '{0} {1} > {2}'.format(self.key, self.value, len(self.children()))


class Resid(NodeAxisTools):

    def custom_print(self):
        return '{0} {1} {2} > {3}'.format(self.key, self.value, self.name, len(self.children()))


class Atom(NodeAxisTools):

    def custom_print(self):
        return '{0} {1} {2} {3}'.format(self.key, self.value, self.name, self.elem)