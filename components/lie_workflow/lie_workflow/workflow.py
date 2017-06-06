# -*- coding: utf-8 -*-

import sys
import time
import threading
import logging
import jsonschema

from   lie_graph      import GraphAxis
from   lie_system     import WAMPTaskMetaData

from   .task_specs    import WORKFLOW_ORM
from   .task_metadata import task_schema
from   .common        import WorkflowError

# Init basic logging
logging.basicConfig(level=logging.DEBUG)

class Workflow(object):
    
    def __init__(self, workflow=None):
        
        # If workflow is defined, load
        if workflow:
            self._init_workflow_spec(workflow)
        else:
            self._init_default_workflow()
            
        # Define task runner
        self.task_runner = None
        self.workflow_thread = None
        self.is_running = False
            
    def _init_default_workflow(self):
        """
        Initiate default workflow
        
        If there is no workflow loaded this method initiates a default
        workflow spec having one Start task.
        """
        
        # Init empty workflow spec as DAG
        self.workflow = GraphAxis()
        self.workflow.orm = WORKFLOW_ORM
        self.workflow.is_directed = True
        self.workflow.node_data_tag = 'task_name'
        
        # Add start node and make root
        nid = self.add_task('start', task_type='Start')
        task_meta = WAMPTaskMetaData()
        
        self.workflow.root = nid
        self.workflow.nodes[self.workflow.root].update(task_meta.dict())
        
        logging.info('Init default empty workflow')
        
    def _init_workflow_spec(self, workflow):
        """
        Initiate predefined workflow
        
        Initiate a workflow from a workflow specification or instance thereof.
        Checks if the workflow defines a root node and if that node is a Start
        task.
        
        :param workflow: Predefined workflow object
        :type workflow:  GraphAxis
        """
        
        self.workflow = workflow
        self.workflow.orm = WORKFLOW_ORM
        
        if self.workflow.root is None:
            raise WorkflowError('Workflow does not have a root node defined')
        
        if self.workflow.nodes[self.workflow.root]['task_type'] != 'Start':
            raise WorkflowError('Workflow root node is not of type Start')
    
    def _error_callback(self, failure, tid):
        """
        Process the output of a failed task and stage the next task to run
        if allowed
        
        :param failure: Twisted deferred error stack trace
        :type failure:  exception
        :param tid:     Task ID of failed task
        :type id:       :py:int
        """
        
        task = self.workflow.getnodes(tid)
        task.active = False
        task.status = 'failed'
        
        logging.error('Task "{0}" ({1}) crashed with error: {2}'.format(task.task_name, task.nid, failure.getErrorMessage()))
        self.is_running = False
        
        return
        
    def _output_callback(self, output, update=True):
        """
        Process the output of a task and stage the next task to run
        
        :param output: Output of the task
        :type output:  JSON
        """
        
        # The data construct returned should be a valid task object
        # according to the task_schema JSON schema
        jsonschema.validate(output, task_schema)
        
        # Update the task data
        if update:
            self.workflow.nodes[output['nid']].update(output)
        
        task = self.workflow.getnodes(output['nid'])
        logging.info('Task "{0}" ({1}), status: {2}'.format(task.task_name, task.nid, task.status))
        
        # If the task is completed, go to next
        next_task_nids = []
        if task.status == 'completed':
            task.active = False
            
            # Get data from previous task and use as input for new task
            task_input = task.get('output')
        
            # Get next task(s) to run
            next_tasks = [t for t in task.children() if task.status != 'disabled']
            if next_tasks:
            
                logging.info('{0} new tasks to run with the output of "{1}" ({2})'.format(len(next_tasks), task.task_name, task.nid))
                for ntask in next_tasks:
                    if not 'input' in ntask.nodes[ntask.nid]:
                        ntask.nodes[ntask.nid]['input'] = {}
                
                    # Should we replace the input with output of previous task
                    if task_input:
                        if ntask.get('replace_input'):
                            ntask.nodes[ntask.nid]['input'] = task_input
                        else:
                            ntask.nodes[ntask.nid]['input'].update(task_input)
                    
                    next_task_nids.append(ntask.nid)
        
        # Step2b: If the task failed, retry if allowed and reset status to "ready"
        if task.status == 'failed' and task.retry_count > 0:
            task.retry_count = task.retry_count - 1
            task.active = False
            task.status = 'ready'
            
            logging.warn('Task "{0}" ({1}) failed. Retry ({2} times left)'.format(task.task_name, task.nid, task.retry_count))
            next_task_nids.append(task.nid)
        
        # If the active failed an no retry is allowed, stop working.
        if task.status == 'failed' and task.retry_count == 0:
            task.active = False
            logging.error('Task "{0}" ({1}) failed'.format(task.task_name, task.nid))
            self.is_running = False
            return
        
        # If the task is completed but a breakpoint is defined, wait for the breakpoint to be lifted
        if task.breakpoint:
            logging.info('Task "{0}" ({1}) finished but breakpoint is active'.format(task.task_name, task.nid))
            self.is_running = False
            return
        
        # Launch new tasks
        for tid in next_task_nids:
            self._run_task(tid)
        
        # If there are no new tasks, return
        if not next_task_nids and self.is_completed:
            logging.info('finished workflow')
            self.is_running = False
            return
    
    def _run_task(self, tid=None):
        """
        Run a task by task ID (tid)
        
        Primary function to run a task using the task_runner registered with
        the class. 
        This function together with the output and error callbacks are run from
        within the task runner thread.
        
        Tasks to run are processed using the following rules:
        
        * If the task is currently active, stop and have the output callback 
          function deal with it.
        * If the task has status 'ready' run it.
        * In all other cases, pass the task data to the output callback
          function. This is usefull for hopping over finished tasks when 
          relaunching a workflow for instance.
        
        :param tid: Task node identifier
        :type tid:  :py:int
        """
        
        # Get the task object from the graph
        task = self.workflow.getnodes(tid)
        
        # Bailout if the task is active
        if task.active:
            logging.debug('Task {0} already active'.format(tid))
            return
        
        # Run the task if ready
        if task.status == 'ready':
            self.is_running = True
            task.active = True
            task.status = 'running'
            
            logging.info('Task "{0}" ({1}), status: {2}'.format(task.task_name, task.nid, task.status))
            task.run_task(self.task_runner, callback=self._output_callback, errorback=self._error_callback)
        
        # In all other cases, pass task data to default output callback.
        else:
            self._output_callback(self.workflow.nodes[tid], update=False)
    
    @property
    def is_completed(self):
        """
        Is the workflow completed successfully or not
        
        :rtype: :py:bool
        """
        
        return all([task['status'] in ('completed','disabled') for task in self.workflow.nodes.values()])
    
    @property
    def failed_task(self):
        
        for task in self.workflow.nodes.values():
            if task.get('status') == 'failed':
                return task['nid']
    
    @property
    def active_breakpoint(self):
        """
        Return task with active breakpoint or None
        """
        
        for task in self.workflow.nodes.values():
            if task.get('breakpoint', False):
                return task['nid']
    
    @property
    def starttime(self):
        """
        Return the start time of the workflow
        """
        
        return self.workflow.nodes[self.workflow.root].get('itime')
        
    @property
    def finishtime(self):
        """
        Return the finish time of the workflow or None if not yet finished
        """
        
        runtimes = [task.get('utime') for task in self.workflow.nodes.values()]
        if None in runtimes:
            return None
        
        return max(runtimes)
    
    @property
    def runtime(self):
        """
        Return the workflow runtime
        """
        
        start = self.starttime
        end = self.finishtime or int(time.time())
        
        return end - start
    
    def cancel(self):
        """
        Cancel a running workflow
        """
        
        if not self.is_running:
            logging.info('Workflow is not running.')
            return
        
        # Get active task
        active_tasks = [task['nid'] for task in self.workflow.nodes.values() if task['active']]
        logging.info('Canceling {0} active tasks in the workflow'.format(len(active_tasks)))
        
        for task in active_tasks:
            self.workflow.nodes[task]['status'] = 'aborted'
            self.workflow.nodes[task]['active'] = False
        
        self.is_running = False
    
    def add_task(self, name, task_type='Task', **kwargs):
        """
        Add a new task to the workflow from the set of supported workflow
        task types defined in the workflow ORM.
        
        After a task of a specific type is added to the graph its init_task
        method is called wich adds default and type specific metadata to
        the node attributes. Additional keyword arguments to the `add_task`
        method are passed to the init_task method.
        
        :param name:      Administrative name of the task
        :type name:       :py:str
        :param task_type: Task type to add
        :type task_type:  :py:str
        :param kwargs:    additonal keyword arguments passed to the task
                          init_task method.
        :type kwargs:     :py:dict
        
        :return:          Task node ID (nid) in the graph
        :rtype:           :py:int
        """
        
        # Task type needs to be supported by ORM
        assert type(task_type) == str, 'Workflow task type needs to be of type string'
        assert task_type in self.workflow.orm.mapped_node_types.get('task_type',[]), 'Workflow task type {0} not supported'.format(task_type)
        
        # Add the task as node
        nid = self.workflow.add_node(name, task_type=task_type)
        
        # Run task initiation, pass additonal keyword arguments
        self.workflow.getnodes(nid).init_task(**kwargs)
        
        return nid
    
    def connect_task(self, task1, task2):
        """
        Connect tasks by name
        
        :param task1: first task of two tasks to connect
        :type task1:  :py:str
        :param task2: second task of two tasks to connect
        :type task3:  :py:str
        """
        
        nid1, nid2 = None, None
        for node in self.workflow.nodes.values():
            if node['task_name'] == task1:
                nid1 = node['_id']
            elif node['task_name'] == task2:
                nid2 = node['_id']
        
        assert nid1, 'Task {0} not in workflow'.format(task1)
        assert nid2, 'Task {0} not in workflow'.format(task2)
        
        self.workflow.add_edge(nid1, nid2)
    
    def step_breakpoint(self, nid):
        
        assert nid in self.workflow.nodes, 'No task with nid {0}'.format(nid)
        assert self.workflow.nodes[nid].get('breakpoint') == True, 'No active breakpoint set on task with nid {0}'.format(nid)
        
        self.workflow.nodes[nid]['breakpoint'] = False
        logging.info('Remove breakpoint on task {0} ({1})'.format(self.workflow.nodes[nid]['task_name'], nid))
                                    
    def input(self, **kwargs):
        """
        Define workflow initial input
        """
        
        assert self.workflow.nodes[self.workflow.root]['task_type'] == 'Start', 'Workflow has no Start node'
        
        self.workflow.nodes[self.workflow.root]['input'] = kwargs
    
    def output(self, tid=None):
        """
        Get workflow output
        
        Returns the output associated to all terminal tasks (leaf nodes) of
        the workflow or of any intermediate tasks identified by the task ID
        
        :param tid: task ID to return output for
        :type tid:  :py:int
        """
        
        if tid and not tid in self.workflow.nodes:
            logging.warn('Unable to return output, no task with ID: {0}'.format(tid))
        
        if tid:
            leaves = self.workflow.getnodes(tid)
        else:
            leaves = self.workflow.leaves()
        
        output = {}
        for task in leaves:
            if task.status == 'completed':
                output[task.nid] = task.output
                
        return output
    
    def metadata(self, data=None, default=None):
        
        metadata = self.workflow.nodes[self.workflow.root]
        if data:
            return metadata.get(data, default)
        
        return metadata
        
    def run(self, tid=None):
        """
        Run the workflow specification or instance thereof untill finished,
        failed or a breakpoint is reached.
        
        A workflow is started from the first 'Start' task and then moves 
        onwards. It can be started from any other task provided that the
        parent task has input defined.
        
        The workflow will be excecuted on a different thread allowing for
        interactivity with the workflow instance while the  workflow is 
        running. 
        
        :param tid:      Start the workflow from task ID
        :type tid:       :py:int
        """
        
        # Start from workflow root by default
        if not tid:
            tid = self.workflow.root
        
        # Check if tid exists
        if not tid in self.workflow.nodes:
            raise WorkflowError('Task with tid {0} not in workflow'.format(tid))
        
        logging.info('Running workflow: {0}, start task ID: {1}'.format(self.metadata('project_title',''), tid))
        
        # If starting at non-root task, check if previous task has output
        parent = self.workflow.getnodes(tid).parent()
        if parent and not 'output' in parent.nodes[parent.nid]:
            logging.error('Parent task to tid {0} (parent {1}) has no output defined'.format(tid, parent.nid))
            return
        
        self.is_running = True
        self.workflow_thread = threading.Thread(target=self._run_task, args=[tid])
        self.workflow_thread.daemon = True
        self.workflow_thread.start()