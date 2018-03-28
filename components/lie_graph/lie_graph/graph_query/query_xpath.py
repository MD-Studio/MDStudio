# -*- coding: utf-8 -*-

"""
file: query_xpath.py

XPath based query of Axis based graphs
"""

import json
import re

from lie_graph import GraphAxis

# Regular expressions
split_filter_chars = re.compile('([\[\]])')
split_path_seperators = re.compile(r'(\.+|/+)')
split_operators = re.compile('([><=*])')


def get_attributes(attr, graph=None):

    # Is the attr a single integer, then use as list item selection
    # Use W3C recommendations, first item index equals 1.
    if len(attr) == 1:
        if isinstance(attr[0], int) and len(graph) > attr[0]:
            return list(graph)[attr[0]]
        if attr[0] == '*':
            return graph

    # Select nodes that have the particular attribute
    sel = [nid for nid in graph.nodes() if attr[0] in graph.nodes[nid]]

    # Match if needed
    if len(attr) == 3:

        operator = attr[1]
        value = attr[2]
        if operator == '=':
            sel = [n for n in sel if graph.nodes[n][attr[0]] == value]
        elif operator == '!=':
            sel = [n for n in sel if graph.nodes[n][attr[0]] != value]
        elif operator == '<':
            sel = [n for n in sel if graph.nodes[n][attr[0]] < value]
        elif operator == '<=':
            sel = [n for n in sel if graph.nodes[n][attr[0]] <= value]
        elif operator == '>':
            sel = [n for n in sel if graph.nodes[n][attr[0]] > value]
        elif operator == '>=':
            sel = [n for n in sel if graph.nodes[n][attr[0]] >= value]
        else:
            pass

    return graph.getnodes(sel)


def get_root(graph, loc=None, exp=None, attr=None):
    """
    Get graph root and query
    """

    root = graph.getnodes(graph.root)
    return root.query_nodes({graph.node_key_tag: exp})


def get_parent(graph, loc=None, exp=None, attr=None):
    """
    Query syntax at start of expression: ..

    Selects the parent of the current node

    :param graph:   (sub)graph to search in
    :param target:  target search predicate
    :return:
    """

    self = get_self(graph, loc=loc, exp=exp, attr=attr)

    if self.nid == graph.root:
        return graph

    return self.parent()


def get_self(graph, loc=None, exp=None, attr=None):
    """
    Defines self and searches in self and children for target

    :param graph:   (sub)graph to search in
    :param target:  target search predicate
    :return:
    """

    if exp not in (None, '*'):
        graph = graph.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        graph = get_attributes(a, graph=graph)

    return graph


def search_child(graph, loc=None, exp=None, attr=None):

    nids = []
    for node in graph:
        nids.extend(node.children().nodes.keys())

    children = graph.getnodes(nids)
    if exp not in (None, '*'):
        children = children.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        children = get_attributes(a, graph=children)

    return children


def search_descendants(graph, loc=None, exp=None, attr=None):

    descendants = graph.descendants(include_self=True)
    if exp not in (None, '*'):
        descendants = descendants.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        descendants = get_attributes(a, graph=descendants)

    return descendants


class XpathExpressionEvaluator(object):

    def __init__(self, sep='/'):

        self.sep = sep

        self.path_root_dict = {sep: get_root, sep * 2: search_descendants, '..': get_parent, '.': get_self}
        self.path_func_dict = {'..': get_parent, '.': get_self, sep: search_child, sep*2: search_descendants}

    def parse_attr(self, attr):

        attr_parse = []
        for a in [n for n in split_operators.split(attr.strip('@')) if len(n)]:
            try:
                attr_parse.append(json.loads(a))
            except:
                attr_parse.append(a)

        return attr_parse

    def parse_xpath_expression(self, expression):

        # Expression should always start with path locator.
        # If not then add self.
        if not expression[0] in ('/', '.'):
            expression = '.{0}'.format(expression)

        # First split based on filter syntax, then process on path locators
        groups = {}
        is_filter = False
        path_counter = 0
        for element in split_filter_chars.split(expression):

            if element == '[':
                is_filter = True
            elif element == ']':
                is_filter = False
            elif not is_filter:
                element = [n for n in split_path_seperators.split(element) if len(n)]
                for group in [element[i:i + 2] for i in range(0, len(element), 2)]:

                    # If only path locator, add empty search wich evaluates to empty graph
                    if len(group) == 1:
                        group.append('')
                    path_counter += 1
                    if group[1].startswith('@'):
                        groups[path_counter] = {'loc': group[0], 'attr': [self.parse_attr(group[1])], 'exp': None}
                    else:
                        groups[path_counter] = {'loc': group[0], 'exp': group[1], 'attr': []}
            elif is_filter:
                groups[path_counter]['attr'].append(self.parse_attr(element))
            else:
                pass

        return groups

    def resolve(self, expression, graph):
        """
        Resolve XPath expression

        :param expression:  XPath expression to evaluate
        :type expression:   :py:str
        :param graph:       GraphAxis instance to apply XPath evaluation on
        :type graph:        :lie_graph:GraphAxis

        :return:            Graph nodes or attributes
        """

        evaluator = self.parse_xpath_expression(expression)

        # Iteratively evaluate
        target = graph

        for i, evald in sorted(evaluator.items()):

            if i == 1 and evald['loc'] in self.path_func_dict:
                target = self.path_root_dict[evald['loc']](target, **evald)
                continue

            # Stop if previous evaluation failed (empty graph, attribute)
            if not isinstance(target, GraphAxis) or target.empty():
                return target

            target = self.path_func_dict.get(evald['loc'])(target, **evald)

        return target
