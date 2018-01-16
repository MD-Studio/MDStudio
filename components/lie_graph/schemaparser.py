# -*- coding: utf-8 -*-

import json
import pprint

from lie_graph import GraphAxis

schema = json.load(open('amber_schema.json'))

def schema_to_dict(schema, dictionary={}):
    """
    Convert a JSON schema based data structure to a Python dictionary
    """
    
    for node in schema.children():
        if node.type == 'object':
            dictionary[node.key] = {}
            schema_to_dict(node, dictionary=dictionary[node.key])
        else:    
            dictionary[node.key] = node.get('default',None)
    
    return dictionary


class SchemaParser(object):
    
    def __init__(self, schema, graph=None):
        
        self.schema = schema
        if not graph:
            self.graph = GraphAxis()
        
        self.graph.node_data_tag = 'key'
        self._schema_to_graph(self.schema)
    
    def _schema_to_graph(self, partial, name=None, edge=None, root_nid=None):
        
        node = dict(items for items in partial.items() if not isinstance(items[1], dict))
        if node:
            if not root_nid:
                nid = self.graph.add_node('root', **node)
                self.graph.root = nid
            else:
                nid = self.graph.add_node(name, **node)
                self.graph.add_edge(root_nid, nid, param=edge)
        else:
            edge = name
            nid = root_nid
            
        for key, value in partial.items():
            if isinstance(value, dict):
                self._schema_to_graph(value, name=key, edge=edge, root_nid=nid)
        
                
g = SchemaParser(schema)
s = g.graph

pp = pprint.PrettyPrinter(indent=2)
pp.pprint(schema_to_dict(s))
# for e in s.nodes.items():
#     print(e)
