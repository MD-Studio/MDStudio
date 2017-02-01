# -*- coding: utf-8 -*-

import os
import StringIO

def _adjacency_to_edges(nodes, adjacency, node_source):
    """
    Construct edges for nodes based on adjacency.
    
    Edges are created for every node in `nodes` based on the neighbors of
    the node in adjacency if the neighbor node is also in `node_source`.
    The source of adjacency information would normally be self.graph and
    self.nodes for `node_source`. However, `node_source may` also equal
    `nodes` to return edges for the isolated graph.
    
    :param nodes:       nodes to return edges for
    :type nodes:        list
    :param adjacency:   node adjacency (self.graph)
    :type adjacency:    dict
    :param node_source: other nodes to consider when creating edges
    :type node_source:  list
    """
    
    edges = []
    for node in nodes:
        edges.extend([tuple([node,e]) for e in adjacency[node] if e in node_source])
    
    return edges

def _edge_list_to_adjacency(edges):
    """
    Create adjacency dictionary based on a list of edges
    
    :param edges: edges to create adjacency for
    :type edges:  list
    """
    
    adjacency = dict([(n,[]) for n in _edge_list_to_nodes(edges)])
    for edge in edges:
        adjacency[edge[0]].append(edge[1])
    
    return adjacency

def _edge_list_to_nodes(edges):
    """
    Create a list of nodes from a list of edges
    
    :param edges: edges to create nodes for
    :type edges:  list
    """
    
    return list(set(sum(edges, ())))

def _make_edges(nodes, directed=True):
    """
    Create an edge tuple from two nodes either directed
    (first to second) or undirected (two edges, both ways).
    
    :param nodes:    nodes to create edges for
    :type nodes:     list or tuple
    :param directed: greate directed edge or not
    :type directed:  bool
    """
    
    edges = [tuple(nodes)]
    if not directed:
        edges.append(nodes[::-1])
    
    return edges

def _open_anything(source, mode='r'):
  """
  Open input available from a file, a Python file like object, standard
  input, a URL or a string and return a uniform Python file like object
  with standard methods.
  
  :param source: Input as file, Python file like object, standard
                 input, URL or a string
  :type source:  mixed
  :param mode:   file access mode, defaults to 'r'
  :type mode:    string
  :return:       Python file like object
  """
  
  # Check if the source is a file and open
  if os.path.isfile(source):
    logger.debug('Reading file from disk {0}'.format(source))
    return open(source, mode)
    
  # Check if source is file already openend using 'open' or 'file' return
  if hasattr(source, 'read'):
    logger.debug('Reading file {0} from file object'.format(source.name))
    return source
    
  # Check if source is standard input
  if source == '-':
    logger.debug('Reading file from standard input')
    return sys.stdin
    
  else:
    # Check if source is a URL and try to open
    try:
      
      import urllib2, urlparse
      if urlparse.urlparse(source)[0] == 'http':
        result = urllib.urlopen(source)
        logger.debug("Reading file from URL with access info:\n {0}".format(result.info()))
        return result
    except:
      logger.info("Unable to access URL")    
    
    # Check if source is file and try to open else regard as string
    try:
      return open(source)
    except:
      logger.debug("Unable to access as file, try to parse as string")
      return StringIO.StringIO(str(source))
      
class GraphException(Exception):
    """
    Graph Exception class.
    Logs the exception as critical before raising.
    """
    
    def __init___(self, message='', *args,**kwargs):
        logger.critical(message)
        Exception.__init__(self, *args,**kwargs)