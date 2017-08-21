# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import threading
import jsonschema
import json
import importlib

from twisted.logger import Logger
from lie_system import WAMPTaskMetaData

from .common import WorkflowError, _schema_to_data
from .workflow_spec import WorkflowSpec

# Get the task schema definitions from the default task_schema.json file
TASK_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'task_schema.json')
task_schema = json.load(open(TASK_SCHEMA_PATH))

logging = Logger()

class _WorkflowQueryMethods(object):
    """
    Mixin class wit helper methods to query workflow global metadata
    """
    
    @property
    def is_running(self):
        """
        Returns the global state of the workflow as running or not.
        
        :rtype: :py:bool
        """
        
        return getattr(self.workflow, 'is_running', False)
    
    @is_running.setter
    def is_running(self, state):
        """
        Set the global state of the workflow as running or not.
        If the new state is 'False' first check if there are no other parallel
        active tasks.
        """
        
        if not state:
            state = len(self.active_tasks) >= 1
        self.workflow.is_running = state
        
    @property
    def is_completed(self):
        """
        Is the workflow completed successfully or not
        
        :rtype: :py:bool
        """
        
        return all([task['status'] in ('completed','disabled') for task in self.workflow.nodes.values()])
    
    @property
    def has_failed(self):
        """
        Did the workflow finish unsuccessfully?
        True if there are no more active tasks and at least one task has failed or was aborted
        """
        
        if not len(self.active_tasks) and len([task['status'] in ('failed','aborted') for task in self.workflow.nodes.values()]):
            return True
        return False
    
    @property
    def starttime(self):
        """
        Return the time stamp at which the workflow was last started
        
        :rtype: :py:int
        """
        
        return getattr(self.workflow, 'start_time', None)
        
    @property
    def finishtime(self):
        """
        Return the time stamp at which the workflow finished or None
        if it has not yet finished
        
        :rtype: :py:int
        """
        
        if not self.is_running:
            return getattr(self.workflow, 'update_time', None)
        return None
    
    def runtime(self, tid=None):
        """
        Return the total workflow runtime in seconds or the
        runtime of a specific task defined by the task ID
        
        :param tid: task for wich to calculate the runtime
        :type tid:  :py:int
        
        :rtype: :py:int
        """
        
        if tid:
            task = self.workflow.getnodes(tid)
            session = task.session
            return session.get('utime',0) - session.get('itime',0)
            
        start = self.starttime or 0
        end = self.finishtime or 0
        if self.is_running:
            end = getattr(self.workflow, 'update_time', int(time.time()))
        
        return end - start
    
    @property
    def active_tasks(self):
        """
        Return all active tasks in the workflow
        
        :rtype: :py:list
        """
        
        return [tid for tid,task in self.workflow.nodes.items() if task['active']]
    
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
    
    def summary(self):
        
        print('task  tid  links  status  runtime  output')
        for tid,task in self.workflow.nodes.items():
            session = task.get('session', {})
            print('{0}  {1}  {2}  {3}  {4}  {5}'.format(
                task['task_name'],
                tid,
                self.workflow.adjacency[tid],
                task['status'],
                session.get('utime',0) - session.get('itime',0),
                task.get('output_data', {})
            ))


class WorkflowRunner(_WorkflowQueryMethods):
    """
    This is the main class for running microservice oriented workflows.
    
    Running a workflow is based on a workflow specification build using the
    `WorkflowSpec` class. Such a workflow can be loaded into the `Workflow`
    class simply by overloading the Workflow.workflow attribute.
    The `Workflow` class also inherits the methods from the `WorkflowSpec`
    class allowing to build specification right from the `Workflow` class
    and even change a running workflow.
    
    The execution of workflow steps is performed on a different thread than
    the main Workflow object allowing the user to interact with the running
    workflow.
    The DAG including the metadata dat is generated while executing the steps
    can be serialized to JSON for persistent storage. The same JSON object is
    used as input to the Workflow class validated by a Workflow JSON schema.
    
    :param workflow:   the workflow DAG to run
    :type workflow:    JSON object
    :param schema_url: URL of the JSON schema describing the DAG
    :type schema_url:  :py:str
    """
    
    def __init__(self):
        
        # Workflow DAG placeholder
        self.workflow = None
        
        # Init inherit classes such as the WorkflowSpec
        super(WorkflowRunner, self).__init__()
        
        # Define task runner
        self.task_runner = None
        self.workflow_thread = None
        
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
        
        failure_message = ""
        if isinstance(failure, Exception):
            failure_message = str(failure)
        else:
            failure.getErrorMessage()
        
        logging.error('Task {0} ({1}) crashed with error: {2}'.format(task.nid, task.task_name, failure_message))
        self.is_running = False
        self.workflow.update_time = int(time.time())
        
        return
        
    def _output_callback(self, output, tid):
        """
        Process the output of a task and stage the next task to run
        
        :param output: output of the task
        :type output:  :py:dict
        
        TODO: what to do if output is returned bit without a session object
              or session object is unchanged? Set a breakpoint and let the
              user check?
        """
        
        # Get the task
        task = self.workflow.getnodes(tid)
        
        # If the task returned no output at all, fail it
        if output:
            # Get session information and remove when done
            session = WAMPTaskMetaData(metadata=output.get('session'))
            del output['session']
        
        else:
            logging.error('Task {0} ({1}) returned no output'.format(task.nid, task.task_name))
            task.status = 'failed'
        
        # Update the task output data only not already 'completed'
        if task.status != 'completed':
            if not 'output_data' in self.workflow.nodes[tid]:
                self.workflow.nodes[tid]['output_data'] = {}
            self.workflow.nodes[tid]['output_data'].update(output)
        
            # Update the task meta data
            task.status = session.status
            self.workflow.nodes[tid]['session'] = session.dict()
            self.workflow.update_time = int(time.time())
        
        logging.info('Task {0} ({1}), status: {2}'.format(task.nid, task.task_name, task.status))
        
        # If the task is completed, go to next
        next_task_nids = []
        if task.status == 'completed':
            task.active = False
            
            # Get data from just completed task and use as input for new task
            task_input = task.get('output_data')
             
            # Get next task(s) to run
            next_tasks = [t for t in task.children() if task.status != 'disabled']
            logging.info('{0} new tasks to run with the output of {1} ({2})'.format(len(next_tasks), task.nid, task.task_name))         
            for ntask in next_tasks:
                if not 'input_data' in ntask.nodes[ntask.nid]:
                    ntask.nodes[ntask.nid]['input_data'] = {}
                
                # Get output/input data mapper
                mapper = self.workflow.edges[(task.nid,ntask.nid)].get('data_mapping', {})
                
                # Should we replace the input with output of previous task
                if task_input:
                    if ntask.get('replace_input', False):
                        ntask.nodes[ntask.nid]['input_data'] = {}
                    
                    # Map output to input
                    for key, value in task_input.items():
                        key = mapper.get(key, key)
                        ntask.nodes[ntask.nid]['input_data'][key] = value
                
                next_task_nids.append(ntask.nid)
        
        # If the task failed, retry if allowed and reset status to "ready"
        if task.status == 'failed' and task.retry_count > 0:
            task.retry_count = task.retry_count - 1
            task.active = False
            task.status = 'ready'
            
            logging.warn('Task {0} ({1}) failed. Retry ({2} times left)'.format(task.nid, task.task_name, task.retry_count))
            next_task_nids.append(task.nid)
        
        # If the active failed an no retry is allowed, stop working.
        if task.status == 'failed' and task.retry_count == 0:
            task.active = False
            logging.error('Task {0} ({1}) failed'.format(task.nid, task.task_name))
            self.is_running = False
            return
        
        # If the task is completed but a breakpoint is defined, wait for the breakpoint to be lifted
        if task.breakpoint:
            logging.info('Task {0} ({1}) finished but breakpoint is active'.format(task.nid, task.task_name))
            self.is_running = False
            return
        
        # Finish of if there are no more tasks to run and all are completed
        if not next_task_nids and (self.is_completed or self.has_failed):
            logging.info('finished workflow')
            self.is_running = False
            return
            
        # Launch new tasks
        for tid in next_task_nids:
            self._run_task(tid)
        
    def _run_task(self, tid):
        """
        Run a task by task ID (tid)
        
        Primary function to run a task using the task_runner registered with
        the class or a custom Python runner function or class. 
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
        
        # Get the task object from the graph. nid is expected to be in graph.
        # Check ifn the task has a 'run_task' method.
        task = self.workflow.getnodes(tid)
        assert hasattr(task, 'run_task'), logging.error('Task {0} ({1}) requires "run_task" method'.format(task.nid, task.task_name))
        
        # Bailout if the task is active
        if task.active:
            logging.debug('Task {0} ({1}) already active'.format(task.nid, task.task_name))
            return
        
        # Run the task if status is 'ready'
        if task.status == 'ready':
            
            # Update the task session
            session = WAMPTaskMetaData()
            if 'authid' in self.workflow.nodes[self.workflow.root]['session']:
                session.authid = self.workflow.nodes[self.workflow.root]['session']['authid']
            self.workflow.nodes[tid]['session'] = session.dict()
            
            # Check if there is 'input' defined
            if not 'input_data' in task:
                
                # Check if previous task has output and use it as input for the current
                parent = task.parent()
                if parent and 'output_data' in parent:
                    logging.info('Use output of parent task to tid {0} ({1})'.format(task.nid, parent.nid))
                    self.input(tid, parent.output_data)
            
            self.is_running = True
            self.workflow.update_time = int(time.time())
            
            # Set workflow task meta-data
            task.active = True
            task.status = 'running'
            
            logging.info('Task {0} ({1}), status: {2}'.format(task.nid, task.task_name, task.status))
            task.run_task(self.load_task_function(task.get('custom_func', None)),
                          callback=self._output_callback,
                          errorback=self._error_callback)
        
        # In all other cases, pass task data to default output callback
        # instructing it to not update the data but decide on the followup
        # workflow step to take. 
        else:
            self._output_callback({'session': task.get('session')}, tid)
        
    def load_task_function(self, class_name):
        """
        Load function that needs to be run with a specific workflow task type
        
        Custom Python function can be run on the local machine using a blocking
        or non-blocking task runner.
        These functions are loaded dynamically ar runtime using the URI of the
        function as stored in the task 'custom_func' attribute. A function URI is 
        defined as a dot-seperated string in wich the last name defines the
        function name and all names in front the absolute or relative path to
        the module containg the function. The module needs to be in the 
        python path.
        
        Example: 'path.to.module.function'
        
        If a global function is defined using the `task_runner` attribute it is
        used as fallback in case a custom function is not defined or cannot be
        loaded.
        
        :param class_name: Python absolute or relative function URI
        :type class_name:  :py:str
        
        :rtype:            function object
        """
        
        if class_name:
            module_name = '.'.join(class_name.split('.')[:-1])
            function = class_name.split('.')[-1]
            
            func = self.task_runner
            try:
                module = importlib.import_module(module_name)
                func = getattr(module, function)
                logging.debug('Load task runner function: {0} from module: {1}'.format(function, module_name))
            except: 
                logging.error('Unable to load task runner function: {0} from module: {1}'.format(function, module_name))
        
            return func
            
        return self.task_runner
        
    def delete(self):
        
        pass
        
    def cancel(self):
        """
        Cancel the full workflow.
        
        This method will send a cancel request to all active tasks in the
        running workflow. Once there are no more active tasks the workflow
        run method will stop and the deamon thread will be closed.
        
        For canceling specific tasks please use the `cancel` function of the
        specific task retrieved using the `WorkflowSpec.get_task` method or 
        workflow graph methods.
        """
        
        if not self.is_running:
            logging.info('Workflow is not running.')
            return
        
        # Get active task
        active_tasks = [task['nid'] for task in self.workflow.nodes.values() if task['active']]
        logging.info('Canceling {0} active tasks in the workflow: {1}'.format(len(active_tasks), active_tasks))
        
        for task in active_tasks:
            self.workflow.nodes[task]['status'] = 'aborted'
            self.workflow.nodes[task]['active'] = False
        
        self.is_running = False
        self.workflow.update_time = int(time.time())
        
    def step_breakpoint(self, tid):
        """
        Continue a workflow at a task that is paused by a breakpoint
        
        :param tid: workflow task ID with active breakpoint
        :type tid:  :py:int
        """
        
        # Do some checks
        if not tid in self.workflow.nodes:
            logging.warn('No task with ID {0} in workflow'.format(tid))
            return
        
        task = self.workflow.getnodes(tid)
        if task.get('breakpoint', False) == False:
            logging.warn('No active breakpoint set on task {0}'.format(tid))
            return
        
        # Remove the breakpoint
        task.breakpoint = False
        logging.info('Remove breakpoint on task {0} ({1})'.format(tid, task.task_name))
                                    
    def input(self, tid=None, **kwargs):
        """
        Define task input and configuration data
        """
        
        if not tid:
            tid = self.workflow.root
            
        if not tid in self.workflow.nodes:
            logging.warn('No task with ID {0} in workflow'.format(tid))
            return
        
        if not 'input_data' in self.workflow.nodes[tid]:
             self.workflow.nodes[tid]['input_data'] = {}
        
        self.workflow.nodes[tid]['input_data'].update(kwargs)
    
    def output(self, tid=None):
        """
        Get workflow output
        
        Returns the output associated to all terminal tasks (leaf nodes) of
        the workflow or of any intermediate tasks identified by the task ID
        
        :param tid: task ID to return output for
        :type tid:  :py:int
        """
        
        if not tid in self.workflow.nodes:
            logging.warn('No task with ID {0} in workflow'.format(tid))
        
        if tid:
            leaves = self.workflow.getnodes(tid)
        else:
            leaves = self.workflow.leaves()
        
        output = {}
        for task in leaves:
            if task.status == 'completed':
                output[task.nid] = task.output_data
                
        return output
    
    def set_wamp_session(self, tid=None, session_data=None):
        """
        Initiate a WAMP session in the (Start) node
        """
        
        if not tid:
            tid = self.workflow.root
        
        task = self.workflow.getnodes(tid)
        return task.update_session(session_data)
    
    def run(self, tid=None):
        """
        Run the workflow specification or instance thereof untill finished,
        failed or a breakpoint is reached.
        
        A workflow is started from the first 'Start' task and then moves 
        onwards. It can be started from any other task provided that the
        parent task was successfully completed.
        
        The workflow will be excecuted on a different thread allowing for
        interactivity with the workflow instance while the workflow is 
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
        
        logging.info('Running workflow: {0}, start task ID: {1}'.format(self.workflow.title, tid))
        
        # (WAMP) session should be defined in the Start task
        start_session = self.workflow.nodes[self.workflow.root].get('session')
        if not start_session:
            self.set_wamp_session()
            logging.info('Initiate session data on Start node')
        
        # Always set is_running to True to allow for immediate interactive use
        # preventing race conditions. If the already running, return
        if self.is_running:
            return
        self.workflow.is_running = True
        
        # Set workflow start time if not defined. Don't rerun to allow
        # continuation of unfinished workflows.
        if not hasattr(self.workflow, 'start_time'):
            self.workflow.start_time = int(time.time())
        
        self.workflow_thread = threading.Thread(target=self._run_task, args=[tid])
        self.workflow_thread.daemon = True
        self.workflow_thread.start()