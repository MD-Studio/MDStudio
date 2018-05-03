# -*- coding: utf-8 -*-

"""
file: task_specs.py

Graph node task classes
"""

import itertools
import logging

from lie_graph.graph_algorithms import dfs_paths
from lie_graph.graph_helpers import renumber_id

# Preload Task definitions from JSON schema in the package schema/endpoints/
TASK_SCHEMA = {'workflow_python_task.v1.json': None, 'workflow_wamp_task.v1.json': None}


class Choice(_TaskBase):

    def run_task(self, runner, callback=None, errorback=None):
        """
        Make a choice for one or more connected task based on
        criteria using the input data.

        :param pos: task to choose when evaluation is positive
        :type pos:  :py:list
        :param neg: task to choose when evaluation is negative
        :type pos:  :py:list
        """

        session = WAMPTaskMetaData(
            metadata=self.nodes[self.nid].get('session', {}))

        finput = self.get_input()
        try:
            output = runner(
                session=session.dict(), **finput)
        except Exception as e:
            if errorback:
                return errorback(e, self.nid)
            else:
                logging.error(
                    'Error in running task {0} ({1})'.format(
                        self.nid, self.key))
                logging.error(e)
                return

        # Disable edges to tasks not in choice_nids
        disabled = []
        choice_nids = output.get('choice', [])
        for task in self.children():
            if not task.nid in choice_nids:
                task.status = 'disabled'
                disabled.append(str(task.nid))
        logging.info('Disabled tasks: {0}'.format(','.join(disabled)))

        output.update(finput)
        callback(output, self.nid)


class Mapper(_TaskBase):
    """
    Mapper class

    Task that parallelises input from an array to all descending tasks or
    upto a task that is assigned to collect the output the task
    lineage created by this mapper class.

    Tasks lineages are duplicated dynamically. The mapping procedure may be
    customized by providing a specialised runner function to the run_task
    method
    """

    def run_task(self, runner=None, callback=None, errorback=None):
        """
        :param runner:    custom mapper function
        :type runner:     function
        :param callback:  workflow runner callback function to pass results to
        :type callback:   function
        :param errorback: workflow runner errorback function to call upon
                          function error
        :type errorback:  function
        """

        map_argument = self.get('mapper_arg', 'mapper')
        task_input = self.get_input()
        if map_argument not in task_input:
            errorback(
                'Task {0} ({1}), mapper argument {2} not in input'.format(
                    self.nid, self.key, map_argument), self.nid)

        mapped = task_input[map_argument]
        if len(mapped):

            logging.info(
                'Task {0} ({1}), {2} items to map'.format(
                    self.nid, self.key, len(mapped)))

            # Get task session
            session = WAMPTaskMetaData(
                metadata=self.nodes[self.nid].get('session'))

            # Get the full descendant lineage from this Mapper task to
            # the Collect task assigned to the mapper
            collector_task = self._full_graph.query_nodes(
                {'to_mapper': self.nid})
            if collector_task:
                maptid = list(itertools.chain.from_iterable(
                    dfs_paths(self._full_graph, self.nid, collector_task.nid)))
                maptid = sorted(set(maptid))
                maptid.remove(self.nid)
                maptid.remove(collector_task.nid)
            else:
                maptid = self.descendants(return_nids=True)

            # Create sub graph of the mapper tasks lineage.
            # Call errorback if no task lineage.
            # A subgraph is a deep copy of the full graph but with all edges.
            # remove edges not having any link to the mapped tasks.
            if maptid:
                subgraph = self._full_graph.getnodes(maptid).copy(clean=False)
                maptidset = set(maptid)
                for edge in list(subgraph.edges.keys()):
                    if not set(edge).intersection(maptidset):
                        subgraph.remove_edge(edge)
            else:
                errorback(
                    'Task {0} ({1}), no tasks connected to Mapper task'.format(
                        self.nid, self.key), self.nid)
                return

            first_task = maptid[0]
            last_task = maptid[-1]
            mapper_data_mapping = self._full_graph.edges[(self.nid, first_task)]
            mapped_children = [first_task]
            for task in range(len(mapped)-1):

                g, tidmap = renumber_id(subgraph, self._full_graph._nodeid)
                self._full_graph += g

                if collector_task:
                    self._full_graph.add_edge(
                        tidmap[last_task], collector_task.nid)

                first_task = tidmap[first_task]
                last_task = tidmap[last_task]
                mapped_children.append(first_task)

            for i, child in enumerate(mapped_children):

                child = self._full_graph.getnodes([child])

                # Define input for the copied task
                if 'input_data' not in child:
                    self._full_graph.nodes[child.nid]['input_data'] = {}

                # Add all other input arguments to
                for key, value in task_input.items():
                    if not key == map_argument:
                        child['input_data'][key] = value

                # List item to dict if needed and perform data mapping
                tomap = mapped[i]
                if not isinstance(tomap, dict):
                    datamap = mapper_data_mapping.get('data_mapping', {})
                    datamap = datamap.get(map_argument, map_argument)
                    tomap = {datamap: tomap}
                child['input_data'].update(tomap)

            session.status = 'completed'
            callback({'session': session.dict()}, self.nid)

        else:
            errorback('Task {0} ({1}), no items to map'.format(
                self.nid, self.key), self.nid)
