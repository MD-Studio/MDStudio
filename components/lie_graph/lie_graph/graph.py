# -*- coding: utf-8 -*-

"""
file: graph.py

Graph base class implementing a graph based data storage with support
for dictionary like storage of data in graph nodes and edges, rich 
graph comparison, query and traversal method and a Object Relations
Mapper.
"""

from   __future__ import unicode_literals

import collections
import copy
import logging as logger
import weakref

from   .graph_dict            import GraphDict
from   .graph_mixin           import NodeTools, EdgeTools
from   .graph_orm             import GraphORM
from   .graph_axis_methods    import node_neighbors
from   .graph_algorithms      import nodes_are_interconnected
from   .graph_math_operations import graph_union, graph_update
from   .graph_helpers         import (GraphException, _adjacency_to_edges, 
                                      _edge_list_to_adjacency, _edge_list_to_nodes, _make_edges)

class Graph(object):
    """
    Graph base class
    
    *Graph root*
    By default a graph is an undirected and non-rooted network of nodes.
    Many graph methods however require the definition of a root relative to
    which a calculation will be performed.
    
    The graph class defines a `root` attribute for this purpose that is 
    undefined by default. It willbe set automatically in the following cases:
    
    * Node traversal: the first node selected (getnodes method) will be assigned 
      root and traversal to `child` nodes will be done relative to the `root`.
      If multiple nodes are selected using `getnodes`, the root node is
      ambiguous and will be set to the node with the lowest _id.
    """
    
    def __init__(self, adjacency=None, nodes=None, edges=None, orm=None):
        """
        Implement class __init__
        
        Initiate empty GraphDict for the adjacency, nodes and edges.
        Update these objects with any adjacency, nodes or edges GraphDict
        objects passed as argument.
        
        :param adjacency:     object that stores the dictionary of node/edges
                              ID pairs. This is the graph adjacency.
                              Adjacency is optional and will be constructed 
                              from edges by default.
        :type adjacency:      GraphDict instance
        :param nodes:         object that stores the dictionary of node ID/node
                              data pairs
        :type nodes:          GraphDict instance
        :param edges:         object that stores the dictionary of edge ID/edge
                              data pairs
        :type edges:          GraphDict instance
        :param orm:           graph Object Relations Mapper
        :type orm:            GraphORM object
        :param is_directed:   Rather the graph is directed or undirected
        :type is_directed:    bool, default False
        :param auto_nid:      Use integers as node ID, automatilcally assigned
                              and internally managed. If False, the node object
                              added will itself be used as node ID as long as
                              it is hashable. In the latter case, nodes are
                              enforced to be unique, duplicate nodes will be
                              ignored.
        :type auto_nid:       bool, default True.
        :param node_data_tag: dictionary key used to store node data
        :type node_data_tag:  str
        :param root:          root node nid used by various methods when
                              traversing the graph in a directed fasion where
                              a notion of a parent is important.
        :type root:           mixed
        """
        
        self.orm   = orm or GraphORM()
        self.nodes = GraphDict(nodes)
        self.edges = GraphDict(edges)
        self.adjacency = GraphDict(adjacency)
        
        # Adjacency is optional and can be constructed from edges.
        if not adjacency and edges:
            self.adjacency = GraphDict(_edge_list_to_adjacency(edges.keys()))
        
        # Graph attributes, set directly
        self.is_directed   = False
        self.is_masked     = False
        self.auto_nid      = True
        self.root          = None
        self.edge_data_tag = 'label'
        self.node_data_tag = 'data'
        self.node_tools    = NodeTools
        self.edge_tools    = EdgeTools
        
        # Graph internal attributes, do not set manually.
        # Automatically assigned node ID's always increment the highest
        # integer ID in the graph
        self._nodeid       = 1
        self._set_auto_nid()
        self._full_graph   = self
        self._initialised  = True
        
    def __add__(self, other):
        """
        Implement class __add__, addition (+).
        
        :param other: other Graph instance
        :return:      new graph combining self and other
        :rtype:       Graph instance
        """
        
        if not isinstance(other, Graph):
            GraphException("Object {0} not instance of Graph base class".format(type(other).__name__))
            return
        
        newgraph = self.copy()
        newgraph = graph_union(newgraph, other)
        
        return graph_update(newgraph, other)
        
    def __contains__(self, other):
        """
        Implement class __contains__
        
        Test if other is identical to, or a subgraph of self with respect to
        its topology (adjacency).
        
        .. warning:: This comparison is based on identity in node ID in the
                     graph adjacency, not node or edge attributes. 
        """
        
        if not isinstance(other, Graph):
            logger.error("Object {0} not instance of Graph base class".format(type(other).__name__))
            return False
        
        other_nodes_keys = set(other.nodes.keys())
        self_nodes_keys = set(self.nodes.keys())
        other_edges_keys = set(other.edges.keys())
        self_edges_keys = set(self.edges.keys())
        
        return all([other_nodes_keys.issubset(self_nodes_keys), other_edges_keys.issubset(self_edges_keys)])
    
    def __copy__(self, memo={}):
        """
        Copy directives for this class
        """
        
        return self.copy()
    
    def __deepcopy__(self, memo={}):
        """
        Deepcopy directives for this class
        """
        
        return self.copy(deep=True)
        
    def __eq__(self, other):
        """
        Implement class __eq__
        
        Evaluate equality based on graph topology (adjacency)
        
        .. warning:: This comparison is based on identity in node ID in the
                     graph adjacency, not node or edge attributes.
        """
        
        if self.adjacency.keys() != other.adjacency.keys():
            return False
        
        return all([set(self.adjacency[i]) == set(other.adjacency[i]) for i in self.adjacency])
      
    def __getitem__(self, key):
        """
        Implement class __getitem__
        
        Return nodes or edges in a (sub)graph by dictionary lookup.
        This function is overloaded in (sub)graphs containing single nodes or
        edges to provide access to node or edge attributes.
        
        :return: nodes or edges.
        :rtype:  Node ID as integer or edge ID as tuple of 2 node ID's.
        """
        
        if type(key) in (tuple,list):
            return self.getedges(key)
        
        return self.getnodes(key)
    
    def __ge__(self, other):
        """
        Implement class __ge__
        
        Evaluate greater-then or equal equality based on graph topology (edges)
        """
        
        return self.edges.keys() >= other.edges.keys()
    
    def __gt__(self, other):
        """
        Implement class __gt__
        
        Evaluate greater-then equality based on graph topology (edges)
        """
        
        return self.edges.keys() > other.edges.keys()
        
    def __iadd__(self, other):
        """
        Implements class __iadd__, inplace addition (+=).
        
        Calls the class `add` method
        
        :param other: other Graph instance
        :return:      self combined with other
        :rtype:       Graph instance
        """
        
        if not isinstance(other, Graph):
            GraphException("Object {0} not instance of Graph base class".format(type(other).__name__))
            return
        
        newgraph = graph_union(self, other)
        
        return graph_update(newgraph, other)
    
    def __isub__(self, other):
        """
        Implement class __isub__, inplace subtraction (-=).
        
        :param other: other Graph instance
        :return:      self with other subtracted
        :rtype:       Graph instance
        """
        
        self.remove_nodes(other.nodes.keys())
        
        return self
    
    def __iter__(self):
        """
        Implement class __iter__
        
        Iterate over nodes using iternodes
        
        :return: number of nodes
        :rtype:  int
        """
        
        return self.iternodes()
    
    def __len__(self):
        """
        Implement class __len__
        
        Represent the length of the grpah as the number of nodes
        
        :return: number of nodes
        :rtype:  int
        """
    
        return len(self.nodes)
    
    def __le__(self, other):
        """
        Implement class __le__
        
        Evaluate less-then or equal to equality based on graph topology (edges)
        """
        
        return self.edges.keys() <= other.edges.keys()
        
    def __lt__(self, other):
        """
        Implement class __lt__
        
        Evaluate less-then equality based on graph topology (edges)
        """
        
        return self.edges.keys() < other.edges.keys()
        
    def __ne__(self, other):
        """
        Implement class __ne__
        
        Evaluate non-equality in graph topology (adjacency)
        
        .. warning:: This comparison is based on identity in node ID in the
                     graph adjacency, not node or edge attributes.
        """
        
        return not self.__eq__(other)
    
    def __repr__(self):
        
        """
        Implement class __repr__
        
        String representation of the class listing node and edge count.
        
        :rtype: string
        """
        
        return '<{0} object {1}: {2} nodes, {3} edges. Directed: {4}>'.format(type(self).__name__,
            id(self), len(self.nodes), len(self.edges), self.is_directed)
    
    def __sub__(self, other):
        """
        Implement class __sub__, subtraction (-).
        
        :param other: other Graph instance
        :return:      new graph with other subtracted
        :rtype:       Graph instance
        """
        
        new_graph = self.copy()
        new_graph.remove_nodes(other.nodes.keys())
        
        return new_graph
        
    @classmethod
    def _get_class_object(cls):
        """
        Returns the current class object. Used by the graph ORM to construct
        new Graph based classes
        """
        
        return cls
        
    def _set_auto_nid(self):
        """
        Set the automatically assigned node ID (nid) based on the nids in the
        current graph
        """
        
        if len(self.adjacency):
            self._nodeid = max([i if type(i) == int else 0 for i in self.adjacency])+1
    
    def _set_full_graph(self, graph):
        
        if isinstance(graph, Graph):
            self._full_graph = weakref.ref(graph._full_graph)()
    
    def add_edge(self, nd1, nd2=None, attr=None, directed=None, deepcopy=True, node_from_edge=False, **kwargs):
        """
        Add edge between two nodes to the graph
        
        An edge is defined as a connection between two node ID's.
        Edge metadata defined as a dictionary allows it to be queried
        by the various graph query functions.
        
        :param nd1 nd2:        edge defined by two node ID's. nd1 may also be
                               an edge tuple/list ignoring nd2
        :type nd1 nd2:         int or tuple/list for nd1
        :param attr:           edge metadata to add
        :type attr:            dict
        :param directed:       override the graph definition for is_directed
                               for the added edge.
        :type directed:        bool, None by default
        :param deepcopy:       make a deepcopy of the node before adding it to
                               the graph.
        :type deepcopy:        bool
        :param node_from_edge: make node for edge node id's not in graph
        :type node_from_edge:  bool, default False
        :param kwargs:         any additional keyword arguments to be added as
                               edge metadata.
        :return:               edge ID
        :rtype:                tuple of two ints
        """
        
        if type(nd1) in (list,tuple):
            nd2 = nd1[1]
            nd1 = nd1[0]
        
        for nodeid in (nd1, nd2):
            if nodeid not in self.adjacency:
                if node_from_edge:
                    self.add_node(nodeid)
                else:
                    assert nodeid in self.adjacency, logger.error('Node with id {0} not in graph.'.format(nodeid))
        
        # Create edge tuples, directed or un-directed (local override possible for mixed graph).
        if directed == None:
            directed = self.is_directed
        edges_to_add = _make_edges((nd1,nd2), directed=directed)
        
        # Prepaire edge data dictionary
        if attr and type(attr) == dict:
            attr.update(kwargs)
        else:
            attr = kwargs
        
        for edge in edges_to_add:
            if edge in self.edges:
                logger.warning('Edge between nodes {0}-{1} exists. Use edge update to change attributes.'.format(*edge))
                continue
            
            # Make a deepcopy of the added attributes
            if deepcopy:
                self.edges[edge] = copy.deepcopy(attr)
            else:
                self.edges[edge] = attr
            
            # Add target node as neighbour of source node in graph adjacency object
            # This operation is always directed.
            if not edge[1] in self.adjacency[edge[0]]:
                self.adjacency[edge[0]].append(edge[1])
            
            logger.debug('Add edge between node {0}-{1} with attributes {2}'.format(edge[0],edge[1],attr))
        
        return edges_to_add[0]
    
    def add_edges(self, edges, **kwargs):
        """
        Add multiple edges to the graph.
        
        This is the iterable version of the add_edge methods allowing
        mutliple edge additions from any iterable.
        
        :param edges: Objects to be added as edges to the graph
        :type edges: Iterable of hashable objects
        :return: list of edge ids for the objects added in the same
               order as th input iterable.
        :rtype: list
        """
        
        if type(edges) == dict:
            edges = [(k[0],k[1],v) for k,v in edges.items()]
        
        edges_added = []
        for e in edges:
            assert len(e) in (2,3), logger.error('Edge needs to contain two nodes and optional arguments, got: {0}'.fomat(e))
            edges_added.append(self.add_edge(*e, **kwargs))
        
        return edges_added
    
    def add_node(self, node, deepcopy=True, **kwargs):
        """
        Add a node to the graph
        
        A node can be any hashable object that is internally represented by
        an automatically assigned node ID that should not be changed (_id).
        The node object is always part of a dictionary in the internal
        database represetation allowing it to be queried by the various
        graph query functions. This allows for the use of custom node
        identifiers.
        
        Additional node metadata can be added add node creation by defining
        them as keyword arguments to the method. If the attributes to add are
        available as dictionary, use Pythons dictionary unpacking (**dict)
        
        :param node:     object representing the node
        :type node:      any hashable object
        :param deepcopy: make a deepcopy of the node before adding it to
                         the graph.
        :type deepcopy:  bool
        :param kwargs:   any additional keyword arguments to be added as
                         node metadata.
        :return:         node ID
        :rtype:          int
        """
        
        # Use internal nid or node as node ID
        if self.auto_nid:
            nid = self._nodeid
        else:
            nid = node
            
            # Node needs to be hashable
            if not isinstance(node, collections.Hashable):
                raise GraphException('Node {0} of type {1} not a hashable object'.format(nid, type(node).__name__))
            
            # Node needs to be unique
            if nid in self.nodes:
                raise GraphException('Node {0} already assigned'.format(nid))
        
        logger.debug('Add node. id: {0}, type: {1}'.format(nid, type(node).__name__))
        
        # Prepaire node data dictionary
        node_data = {'nid':nid, '_id':self._nodeid}
        if deepcopy:
            node_data[self.node_data_tag] = copy.deepcopy(node)
            node_data.update(kwargs)
        else:
            node_data[self.node_data_tag] = node
            node_data.update(copy.deepcopy(kwargs))
        
        self.adjacency[nid] = []
        self.nodes[nid] = node_data
        
        # Always increment internal node ID by 1
        self._nodeid += 1
        
        return nid
    
    def add_nodes(self, nodes, **kwargs):
        """
        Add multiple nodes to the graph.
        
        This is the iterable version of the add_node methods allowing
        mutliple node additions from any iterable.
        
        :param nodes: Objects to be added as nodes to the graph
        :type nodes: Iterable of hashable objects
        :return: list of node ids for the objects added in the same
               order as th input iterable.
        :rtype: list
        """
        
        node_collection = []
        for node in nodes:
            node_collection.append(self.add_node(node, **kwargs))
        
        return node_collection
    
    def attr(self, key):
        """
        Provides direct access to a node or edge attribute by ID.
        
        :return: Node or edge attribute.
        :rtype:  Node ID as integer or edge ID as tuple of 2 node ID's.
        """
        
        if type(key) in (tuple,list):
            key = tuple(key)    
            if self.is_masked:
                return self.edges.get(key)
            return self._full_graph.edges.get(key)
        
        if self.is_masked:
            return self.nodes.get(key)
        return self._full_graph.nodes.get(key)
    
    def clear(self):
        """
        Clear nodes and edges in the graph.
        
        If the Graph instance represents a subgraph, only those nodes and edges
        will be removed.
        """
        
        self.nodes.clear()
        self.edges.clear()
        self.adjacency.clear()
        self._nodeid = 0
                
    def copy(self, deep=True, copy_view=True):
        """
        Return a (deep) copy of the graph
        
        A normal copy is a shallow copy that will copy the class and its 
        attributes except for the nodes, edges and _full_graph objects that
        are referenced.
        
        If 'deep' equals true, a deepcopy of the class and its attributes is
        made. The new graph has _full_graph referenced to itself.
        
        :param deep:        return a deep copy of the Graph object
        :type deep:         bool
        :param copy_view:   make a deep copy of the full nodes, edges and 
                            adjacency dictionary and set any 'views'.
                            Otherwise, only make a deep copy of the 'view'
                            state.
        :type copy_view:    bool
        
        :return:            copy of the graph
        :rtype:             Graph object
        """
        
        # Make a new instance of the current class
        base_cls = self._get_class_object()
        
        # Make a deep copy
        if deep:
            class_copy = base_cls()
            
            class_copy.edges.update(copy.deepcopy(self.edges.dict(return_full=True)))
            if copy_view:
                class_copy.edges._view = copy.deepcopy(self.edges._view)
            
            class_copy.nodes.update(copy.deepcopy(self.nodes.dict(return_full=True)))
            if copy_view:
                class_copy.nodes._view = copy.deepcopy(self.nodes._view)
                
            class_copy.adjacency.update(copy.deepcopy(self.adjacency.dict(return_full=True)))
            if copy_view:
                class_copy.adjacency._view = copy.deepcopy(self.adjacency._view)
                
            class_copy.orm = copy.deepcopy(self.orm)
        
        # Make a shallow copy
        else:
            class_copy = base_cls(adjacency=self.adjacency, nodes=self.nodes, edges=self.edges, orm=self.orm)
            class_copy._full_graph = self._full_graph
            
        # Copy all class attributes except 'adjacency','nodes', 'edges',
        # '_full_graph and orm
        notcopy = ('adjacency','edges','nodes', '_full_graph', 'orm')
        for k,v in self.__dict__.items():
            if not k in notcopy:
                class_copy.__dict__[k] = copy.deepcopy(v)
        
        logger.debug('Return {0} copy of graph {1}'.format('deep' if deep else 'shallow', repr(self)))
        
        return class_copy
    
    def get(self, nid, key=None, defaultattr=None, default=None):
        """
        Return (sub)graph values.
        
        This is a placeholder method that can be overloaded by custom classes
        to return a value for (sub)graphs containing more than one edge or
        node in contrast to the single node or edge graph classes for which 
        the get method returns attribute values.
        The `get` method has the latter functionality by default and will 
        return single node or edge attributes based on nid.
        
        :param nid:         node or edge identifier to return data for. If not
                            defined attempt to resolve using `nid` property.
        :type nid:          mixed
        :param key:         node or edge value attribute name. If not defined
                            then attempt to use class wide `node_data_tag`
                            attribute.
        :type key:          mixed
        :param defaultattr: node or edge value attribute to use as source of
                            default data when `key` attribute is not present.
        :type defaultattr:  mixed
        :param default:     value to return when all fails
        :type default:      mixed
        """
        
        # Return node or edge data
        target = self.attr(nid)
        
        # Get key or default class node/edge data key
        if type(nid) in (tuple,list):
            key = key or self.edge_data_tag
        else:
            key = key or self.node_data_tag
        
        if key in target:
            return target[key]
        return target.get(defaultattr, default)
        
    def getedges(self, edges, orm_cls=None):
        """
        Get an edge as graph object
        
        Returns a new graph view object for the given edge and it's nodes.
        If `is_masked` equals True the new graph object will represent
        a fully isolated subgraph for the edges, the connected nodes and the
        adjacency using views on the respective nodes, edges and adjacency
        GraphDict instances.
        If `is_masked` equals False only the edges GraphDict will represent
        the subgraph as a view but nodes and adjacency will represent the full
        graph. As such, connectivity with the full graph remains.
        
        Getedges calls the Graph Object Relation Mapper (GraphORM) class 
        to customize the returned (sub) Graph class. Next to the custom classes
        registered with the ORM mapper, the `getedges` method allows for
        further customization of the returned Graph object through the 
        orm_cls attribute. In addition, for subgraphs containing single edges,
        the EdgeTools class is added.
        
        :param edge:    edge id
        :type edge:     iterable of length 2 containing intergers
        :param orm_cls: custom classes to construct new edge oriented Graph 
                        class from.
        :type orm_cls:  list
        """
        
        # Coerce to list
        if all([type(e) in (tuple,list) for e in edges]):
            edges = [tuple(e) for e in edges]
        elif len(edges) == 2:
            edges = [tuple(edges)]
        
        # Edges need to be in graph
        if edges:
            edges_not_present = [e for e in edges if not e in self.edges]
            if edges_not_present:
                raise GraphException('Following edges are not in graph {0}'.format(edges_not_present))
        else:
            edges = []
        
        # Build custom class list. Default NodeTools need to be included in
        # case of single nodes and not overloaded in MRO.
        custom_orm_cls = []
        if orm_cls:
            if not isinstance(orm_cls, list):
                raise GraphException('Custom edge classes need to be defined as list')
            custom_orm_cls.extend(orm_cls)
        if len(edges) == 1:
            custom_orm_cls.append(self.edge_tools)
        
        base_cls = self.orm.get(self, edges, self._get_class_object(), classes=custom_orm_cls)
        w = base_cls(adjacency=self.adjacency, nodes=self.nodes, edges=self.edges, orm=self.orm)
        
        w.edges.set_view(edges)
        
        # Get nodes and adjacency for the edge selection if it represents an isolated graph
        if self.is_masked:
            adjacency = _edge_list_to_adjacency(edges)
            w.nodes.set_view(adjacency.keys())
            w.adjacency = GraphDict(adjacency)
        
        # copy class attributes
        for key,value in self.__dict__.items():
            if not key in ('nodes', 'edges', 'orm', 'adjacency'):
                w.__dict__[key] = value
        w._set_full_graph(self)
        
        return w
    
    def getnodes(self, nodes, orm_cls=None):
        """
        Get one or multiple nodes as new subgraph object
        
        Returns a new graph view object for the given node and it's edges.
        If `is_masked` equals True the new graph object will represent
        a fully isolated subgraph for the nodes, the edges that connect them
        and the adjacency using views on the respective nodes, edges and adjacency
        GraphDict instances.
        If `is_masked` equals False only the nodes GraphDict will represent
        the subgraph as a view but edges and adjacency will represent the full
        graph. As such, connectivity with the full graph remains.
        If nodes equals None or empty list, the returned Graph object will have
        no nodes and is basically 'empty'.
        
        Getnodes calls the Graph Object Relation Mapper (GraphORM) class 
        to customize the returned (sub) Graph class. Next to the custom classes
        registered with the ORM mapper, the `getnodes` method allows for
        further customization of the returned Graph object through the 
        orm_cls attribute. In addition, for subgraphs containing single nodes,
        the NodeTools class is added.
        
        :param nodes:   node id
        :type nodes:    int
        :param orm_cls: custom classes to construct new node oriented Graph 
                        class from.
        :type orm_cls:  list
        """
        
        # Coerce to list
        if not type(nodes) in (tuple,list) and nodes:
            nodes = [nodes]
        
        # Nodes need to be in graph
        if nodes:
            nodes_not_present = [n for n in nodes if not n in self.adjacency]
            if nodes_not_present:
                raise GraphException('Following nodes are not in graph {0}'.format(nodes_not_present))
        else:
            nodes = []
        
        # Build custom class list. Default NodeTools need to be included in
        # case of single nodes and not overloaded in MRO.
        custom_orm_cls = []
        if orm_cls:
            if not isinstance(orm_cls, list):
                raise GraphException('Custom node classes need to be defined as list')
            custom_orm_cls.extend(orm_cls)
        if len(nodes) == 1:
            custom_orm_cls.append(self.node_tools)
        
        base_cls = self.orm.get(self, nodes, self._get_class_object(), classes=custom_orm_cls)
        w = base_cls(adjacency=self.adjacency, nodes=self.nodes, edges=self.edges, orm=self.orm)
        
        w.nodes.set_view(nodes)
        
        # Get edges and adjacency for the node selection if it represents an isolated graph
        if self.is_masked:
            edges = _adjacency_to_edges(nodes, self.adjacency, nodes)
            w.edges.set_view(edges)
            
            if edges:
                w.adjacency = GraphDict(_edge_list_to_adjacency(edges))
            else:
                w.adjacency = GraphDict(dict([(n,[]) for n in nodes]))
            
        # copy class attributes
        for key,value in self.__dict__.items():
            if not key in ('nodes', 'edges', 'orm', 'adjacency'):
                w.__dict__[key] = value
        w._set_full_graph(self)
        
        # If root node set and is_masked, reset root to node in new sub(graph)
        # to prevent a root node that is not in the new subgraph.
        # TODO: the newly selected root node is arbitrary and may not be the one closest
        # to the old root node in hierarchy.
        if w.root != None and self.is_masked:
            if w.root not in w.nodes() and len(w.nodes):
                w.root = min([w.nodes[n].get('_id', self._nodeid) for n in w.nodes()])
                
        return w
    
    def insert(self, node, between):
        """
        Insert a new node in between two other
        
        :param node:    node to add
        :param between: nodes to add new node in between  
        """
        
        if len(between) > 2:
            raise Exception('Insert is only able to insert between two nodes')
    
        if nodes_are_interconnected(self, between):
            nid = self.add_node(node)
            for n in between:
                self.add_edge((nid,n))
      
            del self.edges[between]
    
    def iteredges(self, orm_cls=None):
        """
        Graph edge iterator
        
        Returns a new graph view object for the given edge and it's nodes.
        
        :param orm_cls: custom classes to construct new Graph class from for
                        every edge that is returned
        :type orm_cls:  list
        """
          
        for edge in self.edges:
            yield self.getedges(edge, orm_cls=orm_cls)
    
    def iternodes(self, orm_cls=None):
        """
        Graph node iterator
        
        Returns a new graph view object for the given node and it's edges.
        The dynamically created object contains additional node tools.
        
        :param orm_cls: custom classes to construct new Graph class from for
                        every node that is returned
        :type orm_cls:  list
        """
        
        for node in self.nodes:
            yield self.getnodes(node, orm_cls=orm_cls)
                
    def query_edges(self, query, orm_cls=None):    
        """
        Select nodes and edges based on edge data query

        :param query:   dictionary of edge data key/value pairs to query on
        :type query:    dict
        :param orm_cls: custom classes to construct new Graph class from.
        :type orm_cls:  list
        """

        query = set(query.items())
        edges= []
        for edge,attr in sorted(self.edges.items()):
            if all([q in attr.items() for q in query]):
                edges.append(edge)

        return self.getedges(edges, orm_cls=orm_cls)
        
    def query_nodes(self, query, orm_cls=None):    
        """
        Select nodes and edges based on node data query
        
        The `getnodes` method is called for the nodes matching the query
        
        :param query:   dictionary of node data key/value pairs to query
        :type query:    dict
        :param orm_cls: custom classes to construct new Graph class from.
        :type orm_cls:  list
        """

        query = set(query.items())
        nodes = []
        for node,attr in sorted(self.nodes.items()):
            if all([q in attr.items() for q in query]):
                nodes.append(node)
    
        nodes = list(set(nodes))
        return self.getnodes(nodes, orm_cls=orm_cls)
        
    def remove_edge(self, nd1, nd2=None):
        """
        Removing an edge from the graph
        
        Checks if the graph contains the edge, then removes it.
        If the graph is undirectional, try to remove both edges
        of the undirectional pair.
        
        :param nd1 nd2: edge defined by two node ID's. nd1 may also be
                        an edge tuple/list ignoring nd2
        :type nd1 nd2:  int or tuple/list for nd1
        """
        
        if not type(nd1) in (list,tuple):
            nd1 = (nd1,nd2)
        
        # Make edges, directed or undirected based on graph settings
        for edge in _make_edges(nd1, directed=self.is_directed):
            if edge in self.edges:
                # Remove from adjacency list
                if edge[1] in self.adjacency[edge[0]]:
                    self.adjacency[edge[0]].remove(edge[1])
                else:
                    logger.warning('Node {0} not part of edge list node {1}'.format(*edge))
                
                del self.edges[edge]
                logger.debug('Removed edge {0} from graph'.format(edge))
            else:
                logger.warning('Unable to remove edge {0}. No such edge ID'.format(edge))
    
    def remove_edges(self, edges):
        """
        Remove multiple edges from the graph.
        
        This is the iterable version of the remove_edge methods allowing
        mutliple edge removal from any iterable.
        
        :param edges: Iterable of edges to remove
        :type edges: Iterable of edges defined as tuples of two node ID's
        """
        
        for edge in edges:
            self.remove_edge(edge)
    
    def remove_node(self, node):
        """
        Removing a node from the graph
        
        Checks if the graph contains the node and if the node is connected with
        edges. Removes the node and associated edges.
        
        :param node: Node to remove
        :type node: mixed
        """
        
        if node in self.adjacency:
            
            # Get edges connected to node and remove them
            edges = [edge for edge in self.edges if node in edge]
            for edge in edges:
                del self.edges[edge]
            
            # Remove node from other nodes adjacency list
            adj_list = [e for e in _edge_list_to_nodes(edges) if not e == node]
            for adj in adj_list:
              self.adjacency[adj].remove(node)
            
            # Remove node from adjacency and nodes object
            del self.adjacency[node]
            del self.nodes[node]
            
            logger.debug('Removed node {0} with {1} connecting edges from graph'.format(node, len(edges)))
        else:
            logger.warning('Unable to remove node {0}. No such node ID'.format(node))
    
    def remove_nodes(self, nodes):
        """
        Remove multiple nodes from the graph.
        
        This is the iterable version of the remove_node methods allowing
        mutliple nodes to be removed from any iterable.
        
        :param node: Nodes to remove
        :type node: mixed
        """
        
        for node in nodes:
            self.remove_node(node)