# -*- coding: utf-8 -*-

"""
file: haddock_helper_methods.py

Common helper functions used by the haddock data model manipulation functions.
"""

import os
import logging


def resolve_credentials(settings):
    """
    Resolve Haddock server username and password from component
    settings or environment variables

    :param settings: component settings
    :type settings:  :py:dict

    :return:         username, password
    """

    username = settings.get('haddock_username', os.environ.get('HADDOCK_SERVER_USER'))
    password = settings.get('haddock_password', os.environ.get('HADDOCK_SERVER_PW'))

    return username, password


def haddock_validation_warning(instance, message=''):

    haddock_type = instance.get('haddock_type', '')

    logging.warning('ValidationWarning in node "{0}" type "{1}": {2}'.format(instance.path(), haddock_type, message))
    return False


def new_incremented_param_name(basename, currnames, start=1):
    """
    Generate new integer incremented version of the parameter name defined by
    `basename` based on a list of current names in `currnames`.

    :param basename:    base name to increment
    :type basename:     :py:str
    :param currnames:   currently defined names
    :type currnames:    :py:list
    :param start:       integer start
    :type start:        :py:int

    :return:            incremented parameter name
    :rtype:             :py:str
    """

    name = None
    while True:
        name = '{0}{1}'.format(basename, start)
        if not name in currnames:
            break
        start += 1

    return name


def validate_model(model):
    """
    Validate a single data model parameter or a full data model block by
    recursively calling the 'validate' method on each node working from
    the leaf nodes up the tree.

    :param model: part of data model to validate
    :type model:  :lie_graph:GraphAxis

    :return:      overall successful validation
    :rtype:       :py:bool
    """

    allnodes = model.nodes.keys()
    leaves = model.leaves(return_nids=True)
    done = []

    def _walk_ancestors(nodes, success=True):
        parents = []
        for node in nodes:
            node = model.getnodes(node)

            # Continue only if the node was found and it has a 'validate' method
            if not node.empty() and hasattr(node, 'validate'):
                val = node.validate()
                done.append(node.nid)
                if not val:
                    return False

                pnid = node.parent().nid
                if not pnid in done and pnid in allnodes:
                    parents.append(pnid)

        if parents:
            return _walk_ancestors(set(parents), success=success)
        return success

    # Recursively walk the tree from leaves up to root.
    return _walk_ancestors(leaves)