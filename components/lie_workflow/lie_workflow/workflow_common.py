# -*- coding: utf-8 -*-

import logging
import itertools

from collections import Counter


class WorkflowError(Exception):

    def __init__(self, message):

        super(WorkflowError, self).__init__(message)

        logging.error(message)


def concat_dict(dict_list):
    """
    Concatenate list of dictionaries to one new dictionary

    Duplicated keys will have their values combined as list.

    :param dict_list:   list of dictionaries to concatenate into a new dict
    :type dict_list:    :py:list

    :return:            Concatenated dictionary
    :rtype:             :py:dict
    """
    keys = list(itertools.chain.from_iterable([d.keys() for d in dict_list]))
    key_count = Counter(keys)
    concatenated = dict([(k, None) if c == 1 else (k, []) for k, c in key_count.items()])

    for d in dict_list:
        for k, v in d.items():
            if key_count[k] > 1:
                concatenated[k].append(v)
            else:
                concatenated[k] = v

    return concatenated


def validate_workflow(workflow):
    """
    Validate the constructed workflow

    :param workflow: Workflow graph to validate
    :type workflow:  :lie_graph:GraphAxis

    :return: Validated or not
    :rtype:  :py:bool
    """

    validated = True

    # Required in case the workflow has only one task
    # TODO: fix this, behaviour due to GraphAxis iterator that iterates
    # children if only one top level element.
    tasks = workflow.query_nodes(format='task')
    if len(tasks) == 1:
        tasks = [tasks]

    # All Task objects should have a 'run_task' method
    for task in tasks:
        if not hasattr(task, 'run_task'):
            logging.warning('Task {0} ({1}) has no "run_task" method'.format(task.nid, task.key))
            validated = False

        if not task.validate():
            validated = False

    return validated
