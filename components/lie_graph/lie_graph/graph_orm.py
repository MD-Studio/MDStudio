# -*- coding: utf-8 -*-

"""
file: graph_orm.py

Defines the Graph Object Relation Mapper (ORM)
"""

import inspect
import logging


class GraphORM(object):

    __slots__ = ('_node_orm_mapping', '_edge_orm_mapping', 'class_name', 'inherit')

    def __init__(self, inherit=True):

        self._node_orm_mapping = {}
        self._edge_orm_mapping = {}
        self.class_name = 'Graph'
        self.inherit = inherit

    def _class_factory(self, base_cls, classes, exclude_node_edge=False):
        """
        Factory for custom Graph classes

        Build custom Graph class by adding classes to base_cls.
        The factory resolves the right method resolution order (mro).

        :param base_cls:          graph base class. Needs to be based on Graph
        :type base_cls:           Graph (inherited) class
        :param classes:           additional classes to include in base class
                                  when building custom Graph class
        :type classes:            list or tuple
        :param exclude_node_edge: prevent inheriting from node/edge classes if
                                  returning interface to multiple nodes/edges
        :type exclude_node_edge:  :py:bool

        :return:                  custom Graph class
        :rtype:                   class
        """

        # Get method resolution order for the base_cls,
        # exclude ORM build classes
        base_cls_mro = [c for c in base_cls.mro() if not self.__module__ == c.__module__]

        # Inherit previous custom modules or only graph module classes
        if not self.inherit:
            base_cls_mro = [c for c in base_cls_mro if c.__module__.startswith('lie_graph')]

        # Prevent inheritance of node/edge tools for instance for a query
        # returning multiple nodes called from a single node object.
        if exclude_node_edge:
            base_cls_mro = [n for n in base_cls_mro if '__isnetbc__' not in dir(n)]

        # Add custom classes to the base class mro
        for n in reversed(classes):
            if n not in base_cls_mro:
                base_cls_mro.insert(0, n)

        # Build the new base class
        base_cls_name = base_cls.__name__ or self.class_name
        return type(base_cls_name, tuple(base_cls_mro), {})

    @staticmethod
    def _map_attributes(mapper):

        matching_rules = {}
        for rules in [orm_map['mapping'] for orm_map in mapper.values()]:
            for rule in rules:
                if rule[0] not in matching_rules:
                    matching_rules[rule[0]] = []
                matching_rules[rule[0]].append(rule[1])

        return matching_rules

    @staticmethod
    def _collect_matching_rules(args, kwargs):

        matching_rules = kwargs.items()
        for arg in args:
            if isinstance(arg, dict):
                matching_rules.extend(arg.items())
            elif isinstance(arg, tuple):
                matching_rules.append(arg)

        return matching_rules

    @property
    def mapped_node_types(self):
        """
        Returns a dictionary with all mapped node attributes
        """

        return self._map_attributes(self._node_orm_mapping)

    @property
    def mapped_edge_types(self):
        """
        Returns a dictionary with all mapped edge attributes
        """

        return self._map_attributes(self._edge_orm_mapping)

    def query(self, graph, target, mapping):
        """
        Set based key/value pair matching

        Simple query that performs a literal match node or edge attributes
        and mapped attribute key/value pairs using set based intersection
        operation.

        :param graph:    a graph to match against
        :type graph:     :lie_graph:graph:Graph
        :param target:   nodes or edges
        :type target:    :py:list
        :param mapping:  node or edge mapping
        :type mapping:   :py:dict

        :return:         mapped custom classes
        :rtype:          :py:list
        """

        # Get the node/edge attributes to match against
        query = []
        for i in target:
            query.extend([(k, v) for k, v in graph.attr(i).items() if not type(v) in (list, dict)])

        # query matching based on set operation, does not work for unhashable types
        try:
            query = set(query)
        except TypeError:
            logging.error('Unable to build query')
            query = set([])

        # Match and sort mapped classes according to preferred MRO order (mro_pos)
        orm_mapids = [(mapdict['mro_pos'], mapdict['class']) for mapdict in mapping.values() if
                      mapdict['mapping'].intersection(query)]
        orm_classes = [c[1] for c in sorted(orm_mapids)]

        return orm_classes

    def map_node(self, cls, *args, **kwargs):
        """
        Map a class to a node based on node attributes.

        A mapped class is included in a new Graph or GraphAxis class by the ORM
        class factory based on a match in a node attribute query.
        A query consists of one or multiple keyword arguments for which the
        query engine will calculate a match. The keyword arguments are converted
        into tuples handled by the query engine.
        This method therefore accepts any combination of dictionaries, tuples
        and plain keyword arguments as input to construct query tuples from.

        The ORM class factory consumes multiple custom classes assigned to the
        same node following Pythons Method Resolution Order (MRO) to resolve
        method inheritance.
        Use the `mro_pos` argument to influence the sort order of resolved
        classes in the MRO following the rule: smaller indices are resolved
        first by the MRO. The mro_pos index may be both a negative to large
        positive number to force first or last resolution respectively.

        The mro_pos argument is important for classes defining similar
        named methods to resolve the right method behaviour and when using
        Pythons build-in 'super' function or the @mro_super decorator to call
        similar named method up the MRO stack.

        Every node mapped using the `map_node` method results in a unique map.
        Use the `update_map_node` method to update an existing mapping using the
        map ID.

        :param cls:        class to map
        :type cls:         :py:class
        :param mro_pos:    prefered index of class in Python MRO
        :type mro_pos:     :py:int
        :param args:       node attributes to match
        :type args:        :py:dict or :py:tuple
        :param kwargs:     additional keyword arguments to add to matching
                           dictionary

        :return:           Node mapping identifier
        :rtype:            :py:int
        """

        assert inspect.isclass(cls), TypeError('cls attribute is not a class')

        # Get mro_pos argument
        mro_pos = 0
        if 'mro_pos' in kwargs:
            mro_pos = kwargs.pop('mro_pos')

        # Collect all matching rules
        matching_rules = self._collect_matching_rules(args, kwargs)

        # Add to node mapping dictionary
        node_mapper_id = len(self._node_orm_mapping) + 1
        self._node_orm_mapping[node_mapper_id] = {'mro_pos': mro_pos,
                                                  'class': cls,
                                                  'mapping': set(matching_rules)}
        return node_mapper_id

    def map_edge(self, cls, *args, **kwargs):
        """
        Map a class to an edge based on edge attributes.

        A mapped class is included in a new Graph or GraphAxis class by the ORM
        class factory based on a match in a edge attribute query.
        A query consists of one or multiple keyword arguments for which the
        query engine will calculate a match. The keyword arguments are converted
        into tuples handled by the query engine.
        This method therefore accepts any combination of dictionaries, tuples
        and plain keyword arguments as input to construct query tuples from.

        The ORM class factory consumes multiple custom classes assigned to the
        same edge following Pythons Method Resolution Order (MRO) to resolve
        method inheritance.
        Use the `mro_pos` argument to influence the sort order of resolved
        classes in the MRO following the rule: smaller indices are resolved
        first by the MRO. The mro_pos index may be both a negative to large
        positive number to force first or last resolution respectively.

        The mro_pos argument is important for classes defining similar
        named methods to resolve the right method behaviour and when using
        Pythons build-in 'super' function or the @mro_super decorator to call
        similar named method up the MRO stack.

        Every edge mapped using the `map_edge` method results in a unique map.
        Use the `update_map_edge` method to update an existing mapping using the
        map ID.

        :param cls:        class to map
        :type cls:         :py:class
        :param mro_pos:    prefered index of class in Python MRO
        :type mro_pos:     :py:int
        :param args:       edge attributes to match
        :type args:        :py:dict or :py:tuple
        :param kwargs:     additional keyword arguments to add to matching
                           dictionary

        :return:           Edge mapping identifier
        :rtype:            :py:int
        """

        assert inspect.isclass(cls), TypeError('cls attribute is not a class')

        # Get mro_pos argument
        mro_pos = 0
        if 'mro_pos' in kwargs:
            mro_pos = kwargs.pop('mro_pos')

        # Collect all matching rules
        matching_rules = self._collect_matching_rules(args, kwargs)

        # Add to node mapping dictionary
        edge_mapper_id = len(self._edge_orm_mapping) + 1
        self._edge_orm_mapping[edge_mapper_id] = {'mro_pos': mro_pos,
                                                  'class': cls,
                                                  'mapping': set(matching_rules)}
        return edge_mapper_id

    def update_nodes(self, orm):
        """
        Update the current node orm mapping with those defined by another orm
        instance

        :param orm: Source orm class to update from
        :type orm:  GraphORM
        """

        assert isinstance(orm, GraphORM), 'Requires GraphORM class to update from'

        # Update node mapping for all unique mappings in other ORM
        to_add = []
        for other_id, other_mapping in orm._node_orm_mapping.items():
            similar = False
            for self_mapping in self._node_orm_mapping.values():
                if other_mapping['class'] == self_mapping['class'] and other_mapping['mapping'] == self_mapping['mapping']:
                    similar = True

            if not similar:
                to_add.append(other_id)

        for map_id in to_add:
            node_mapper_id = len(self._node_orm_mapping) + 1
            self._node_orm_mapping[node_mapper_id] = orm._node_orm_mapping[map_id]

    def update_edges(self, orm):
        """
        Update the current edges orm mapping with those defined by another orm
        instance

        :param orm: Source orm class to update from
        :type orm:  GraphORM
        """

        assert isinstance(orm, GraphORM), 'Requires GraphORM class to update from'

        # Update edge mapping for all unique mappings in other ORM
        to_add = []
        for other_id, other_mapping in orm._edge_orm_mapping.items():
            similar = False
            for self_mapping in self._edge_orm_mapping.values():
                if other_mapping['class'] == self_mapping['class'] and other_mapping['mapping'] == self_mapping['mapping']:
                    similar = True

            if not similar:
                to_add.append(other_id)

        for map_id in to_add:
            node_mapper_id = len(self._edge_orm_mapping) + 1
            self._node_orm_mapping[node_mapper_id] = orm._edge_orm_mapping[map_id]

    def get_nodes(self, graph, nodes, classes=None):
        """
        Resolve mapped nodes

        Node mapping and construction of custom classes is only performed when
        a single node is provided.
        For multiple nodes or when the query yields no result, the same class
        is returned base on the Graph instance making the call to the get
        method including any custom classes defined.

        :param graph:    a graph to match against
        :type graph:     :lie_graph:graph:Graph
        :param nodes:    one or more nodes
        :type nodes:     :py:list
        :param classes:  additional classes to include in the base class when
                         building the custom Graph class
        :type classes:   :py:list or :py:tuple

        :return:         new Graph class instance
        """

        if len(nodes) > 1:
            customcls = classes or []
            return self._class_factory(graph._get_class_object(), customcls, exclude_node_edge=True)

        # Perform query
        orm_classes = self.query(graph, nodes, self._node_orm_mapping)

        # If custom classes
        if classes:
            orm_classes.extend(classes)

        # Build new (custom) Graph class
        return self._class_factory(graph._get_class_object(), orm_classes)

    def get_edges(self, graph, edges, classes=None):
        """
        Resolve mapped edges

        Edge mapping and construction of custom classes is only performed when
        a single edge is provided.
        For multiple edges or when the query yields no result, the same class
        is returned base on the Graph instance making the call to the get
        method including any custom classes defined.

        :param graph:    a graph to match against
        :type graph:     :lie_graph:graph:Graph
        :param edges:    one or more edges
        :type edges:     :py:list
        :param classes:  additional classes to include in the base class when
                         building the custom Graph class
        :type classes:   :py:list or :py:tuple

        :return:         new Graph class instance
        """

        if len(edges) > 1:
            customcls = classes or []
            return self._class_factory(graph._get_class_object(), customcls, exclude_node_edge=True)

        # Perform query
        orm_classes = self.query(graph, edges, self._edge_orm_mapping)

        # If custom classes
        if classes:
            orm_classes.extend(classes)

        # Build new (custom) Graph class
        return self._class_factory(graph._get_class_object(), orm_classes)
