# -*- coding: utf-8 -*-

"""
file: graph_orm.py

Defines the Graph Object Relation Mapper (ORM)
"""

import inspect
import logging


class GraphORM(object):

    def __init__(self, inherit=True):

        self._node_orm_mapping = {}
        self._edge_orm_mapping = {}
        self._class_name = 'Graph'
        self._inherit = inherit

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
        if not self._inherit:
            base_cls_mro = [c for c in base_cls_mro if c.__module__.startswith('lie_graph')]

        # Prevent inheritance of node/edge tools for instance for a query
        # returning multiple nodes called from a single node object.
        if exclude_node_edge:
            base_cls_mro = [n for n in base_cls_mro if '__isnetbc__' not in dir(n)]

        # Add custom classes to the base class mro
        for n in reversed(classes):
            if n not in base_cls_mro:
                base_cls_mro.insert(0, n)
        #print(base_cls_mro)
        # Build the new base class
        base_cls_name = base_cls.__name__ or self._class_name
        base_cls = type(base_cls_name, tuple(base_cls_mro), {})
        return base_cls

    def _create_map_id(self, mapper):

        id = len(mapper) + 1
        while id in mapper:
            id += 1

        return id

    @staticmethod
    def _map_attributes(mapper):

        matching_rules = {}
        for rules in [map['mapping'] for map in mapper.values()]:
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
        node_mapper_id = self._create_map_id(self._node_orm_mapping)
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
        edge_mapper_id = self._create_map_id(self._edge_orm_mapping)
        self._edge_orm_mapping[edge_mapper_id] = {'mro_pos': mro_pos,
                                                  'class': cls,
                                                  'mapping': set(matching_rules)}
        return edge_mapper_id

    def update(self, orm):
        """
        Update the current node and edge orm mapping with those defined by
        another orm instance

        :param orm: Source orm class to update from
        :type orm:  GraphORM
        """

        assert isinstance(orm, GraphORM), 'Requires GraphORM class to update from'

        # Update node mapping
        for node_cls, node_map in orm._node_orm_mapping.items():
            if node_cls not in self._node_orm_mapping:
                self._node_orm_mapping[node_cls] = node_map
            else:
                mapping = list(self._node_orm_mapping[node_cls])
                if node_map in mapping:
                    logging.warning('Reassign node mapping {0}'.format(node_map))
                mapping.append(node_map)
                self._node_orm_mapping[node_cls] = set(mapping)

        # Update edge mapping
        for edge_cls, edge_map in orm._edge_orm_mapping.items():
            if edge_cls not in self._edge_orm_mapping:
                self._edge_orm_mapping[edge_cls] = edge_map
            else:
                mapping = list(self._edge_orm_mapping[edge_cls])
                if edge_map in mapping:
                    logging.warning('Reassign edge mapping {0}'.format(edge_map))
                mapping.append(edge_map)
                self._edge_orm_mapping[edge_cls] = set(mapping)

    def resolve_mro(self, graph, objects, classes=None):

        # Are we matching edges or nodes?
        is_edges = all([type(i) in (tuple, list) for i in objects])
        if not is_edges:

            is_nodes = all([type(i) in (int, str, unicode) for i in objects])
            assert is_nodes, 'Query need to be only nodes or only edges not mixed.'

        if len(objects) > 1:
            customcls = classes or []
            return self._class_factory(graph._get_class_object(), customcls, exclude_node_edge=True)

        # Get the node/edge attributes to match against
        query = []
        for i in objects:
            query.extend([(k, v) for k, v in graph.attr(i).items() if not type(v) in (list, dict)])

        # query matching based on set operation, does not work for unhashable types
        try:
            query = set(query)
        except TypeError:
            logging.error('Unable to build query')
            query = set([])

        # Use node or edge mapping dictionary
        mapper = self._node_orm_mapping
        if is_edges:
            mapper = self._edge_orm_mapping

        # Match
        orm_mapids = [(mapdict['mro_pos'], mapdict['class']) for mapdict in mapper.values() if mapdict['mapping'].intersection(query)]
        orm_classes = [c[1] for c in sorted(orm_mapids)]

        # If custom classes
        if classes:
            orm_classes.extend(classes)

        return orm_classes

    def get(self, graph, objects, classes=None):
        """
        Resolve mapped node or edge classes.

        TODO: extend matching engine to match only key or values and use logical operators on values.
        TODO: now only match single objects to prevent 'unambiguous' mapping

        If there is nothing to map, return the base class which by default is
        the same class as the Graph instance making the call to the get method.

        :param graph:                       a graph to match against
        :type graph:                        `lie_graph.graph.Graph`
        :param objects:                     one or more nodes or edges to match against
        :type objects:                      list
        :param classes:                     additional classes to include in base class when
                                            building custom Graph class
        :type classes:                      list or tuple
        """

        # Are we matching edges or nodes?
        is_edges = all([type(i) in (tuple, list) for i in objects])
        if not is_edges:

            is_nodes = all([type(i) in (int, str, unicode) for i in objects])
            assert is_nodes, 'Query need to be only nodes or only edges not mixed.'

        if len(objects) > 1:
            customcls = classes or []
            return self._class_factory(graph._get_class_object(), customcls, exclude_node_edge=True)

        # Get the node/edge attributes to match against
        query = []
        for i in objects:
            query.extend([(k, v) for k, v in graph.attr(i).items() if not type(v) in (list, dict)])

        # query matching based on set operation, does not work for unhashable types
        try:
            query = set(query)
        except TypeError:
            logging.error('Unable to build query')
            query = set([])

        # Use node or edge mapping dictionary
        mapper = self._node_orm_mapping
        if is_edges:
            mapper = self._edge_orm_mapping

        # Match
        orm_mapids = [(mapdict['mro_pos'], mapdict['class']) for mapdict in mapper.values() if mapdict['mapping'].intersection(query)]
        orm_classes = [c[1] for c in sorted(orm_mapids)]

        # If custom classes
        if classes:
            orm_classes.extend(classes)

        return self._class_factory(graph._get_class_object(), orm_classes)
