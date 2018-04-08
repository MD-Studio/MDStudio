# -*- coding: utf-8 -*-

"""
file: query_xpath.py

XPath based query of Axis based graphs.
"""

import json
import re
import logging

from lie_graph.graph import Graph
from lie_graph.graph_axis.graph_axis_methods import node_children, node_ancestors, node_parent

# Regular expressions
split_filter_chars = re.compile(r'([\[\]])')
split_path_seperators = re.compile(r'(\.+|/+)')
split_operators = re.compile(r'(>=|<=|!=|=|<|>|\*)')


def get_attributes(attr, graph=None):
    """
    Graph node attribute query evaluation

    :param attr:
    :param graph:
    :return:
    """

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
    Get graph root and query.

    This is the absolute root of the graph.

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in root
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    root = graph._full_graph.getnodes(graph.root)
    return root.query_nodes({graph.node_key_tag: exp})


def get_parent(graph, loc=None, exp=None, attr=None):
    """
    Query syntax at start of expression: ..

    Selects the parent of the current node

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in parent
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    self = get_self(graph, loc=loc, exp=exp, attr=attr)

    nids = []
    for nid in self.nodes.keys():
        if nid == graph.root:
            nids.append(nid)
        else:
            nids.append(node_parent(self, nid, graph.root))

    return graph.getnodes(nids)


def get_self(graph, loc=None, exp=None, attr=None):
    """
    Defines self and searches in self and children for target

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in self and children
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    if exp not in (None, '*'):
        graph = graph.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        graph = get_attributes(a, graph=graph)

    return graph


def search_child(graph, loc=None, exp=None, attr=None):
    """
    Search graph children linage including self.

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in children
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    nids = []
    for nid in graph.nodes.keys():
        nids.extend(node_children(graph, nid, graph.root))

    children = graph.getnodes(nids)
    if exp not in (None, '*'):
        children = children.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        children = get_attributes(a, graph=children)

    return children


def search_descendants(graph, loc=None, exp=None, attr=None):
    """
    Search graph descendant linage including self.

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in descendants
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    descendants = graph.descendants(include_self=True)
    if exp not in (None, '*'):
        descendants = descendants.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        descendants = get_attributes(a, graph=descendants)

    return descendants


def search_siblings(graph, loc=None, exp=None, attr=None):
    """
    Search graph siblings linage.

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in siblings
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    siblings = graph.siblings()
    if exp not in (None, '*'):
        siblings = siblings.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        siblings = get_attributes(a, graph=siblings)

    return siblings


def search_ancestors(graph, loc=None, exp=None, attr=None):
    """
    Search graph ancestors linage.

    :param graph: (sub)graph instance to search
    :param loc:   path location identifier
    :type loc:    :py:str
    :param exp:   expression to query for in ancestors
    :type exp:    :py:str
    :param attr:  attributes to evaluate for matched expressions
    :type attr:   :py:list

    :return:      query result graph
    :rtype:       :lie_graph:GraphAxis
    """

    nids = []
    for nid in graph.nodes.keys():
        nids.extend(node_ancestors(graph, nid, graph.root))

    ancestors = graph._full_graph.getnodes(list(set(nids)))
    if exp not in (None, '*'):
        ancestors = ancestors.query_nodes({graph.node_key_tag: exp})

    for a in attr:
        ancestors = get_attributes(a, graph=ancestors)

    return ancestors


class XpathExpressionEvaluator(object):

    def __init__(self, sep='/'):
        """
        XpathExpressionEvaluator class

        XPath expression evaluator for GraphAxis queries supporting a common
        subset of XPath functionality in XPath version 3.0 as defined by W3C
        in the specification; https://www.w3.org/TR/xpath-30/

        **Important differences**
        In contrast to the W3C XPath specification, this class always returns
        a GraphAxis object representing the query results even if specific
        attribute values are requested. This is to ensure that all the graph
        and/or node functions become available to the user.
        An empty GraphAxis object means that the XPath query evaluation did not
        yield any result. If it is not empty it guaranties to represent the
        XPath expression even if specific attributes are queried for. In the
        later case the user will have to get the value(s) of the attribute(s)
        from the results.

        **What is supported**

        * XPath location path expressions: '/' = from document root, '//'
          = everywhere in the document, '.' = self, '..' = parent.
        * XPath attribute lookup: '@attr' = select node if it has 'attr'
          attribute, '@attr = "one"' select if attr value equals 'one'.
        * XPath wildcard usage: '*' = select every node or '@*' every attribute
        * XPath index selection: '[2]' = select item with index 2 in the list
          of matching items.
        * XPath axis selectors: 'child', 'descendant', 'self', 'ancestor',
          'ancestor-or-self', 'following-sibling', 'parent'

        **What is not supported**

        * XPath functions expressed as: fn:function-name(XPath expression).
          Functions should be handled in Python using the expression results
          afterwards.

        The evaluator supports different path location separator characters.
        This is the '/' character by default as defined by the W3C XPath
        standard. Changing it to '.' separator allows for emulating Python
        chained attribute lookup.

        :param sep: path separator character
        :type sep:  :py:str
        """

        self.sep = sep

        self.path_root_dict = {sep: get_root, sep * 2: search_descendants, '..': get_parent, '.': get_self}
        self.path_func_dict = {'..': get_parent, '.': get_self, sep: search_child, sep*2: search_descendants}
        self.path_axis_dict = {'child': search_child, 'descendant': search_descendants, 'self': get_self,
                               'following': None, 'following-sibling': search_siblings, 'descendant-or-self': None,
                               'parent': get_parent, 'ancestor': search_ancestors, 'preceding-sibling': None,
                               'preceding': None, 'ancestor-or-self': search_ancestors}

        self.path_root_dict.update(self.path_axis_dict)
        self.path_func_dict.update(self.path_axis_dict)

    def parse_attr(self, attr):
        """
        Parse XPath attribute definitions
        """

        attr_parse = []
        for a in [n for n in split_operators.split(attr.strip('@')) if len(n)]:
            try:
                attr_parse.append(json.loads(a))
            except ValueError:
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

                    # If only path locator, add empty search which evaluates to empty graph
                    if len(group) == 1:
                        group.append('')
                    path_counter += 1

                    # Parse XPath axis
                    if '::' in group[1]:
                        group = group[1].split('::')

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

        Always returns a graph that can be empty if the XPath evaluation
        failed.

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
            if not isinstance(target, Graph) or target.empty():
                return target

            # Parse path segment using appropriate path function
            if evald['loc'] in self.path_func_dict:
                target = self.path_func_dict.get(evald['loc'])(target, **evald)
            else:
                logging.warning('XPath syntax error: "{0}" no valid expression in {1}'.format(evald['loc'], expression))
                target = graph.getnodes(None)

        return target
