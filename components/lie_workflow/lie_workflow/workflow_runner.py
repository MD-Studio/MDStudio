# -*- coding: utf-8 -*-

import os
import threading
import logging

from autobahn.wamp.exception import ApplicationError
from twisted.python.failure import Failure

from lie_workflow.workflow_common import WorkflowError, concat_dict, validate_workflow
from lie_workflow.workflow_spec import WorkflowSpec

from twisted.logger import Logger
logging = Logger()


class WorkflowRunner(WorkflowSpec):
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
    """

    def __init__(self, workflow=None, **kwargs):

        # Init inherit classes such as the WorkflowSpec
        super(WorkflowRunner, self).__init__(workflow=workflow, **kwargs)

        # Define task runner
        self.task_runner = None
        self.workflow_thread = None

        # Workflow state
        self._is_running = False

    def _collect_input(self, task):
        
        # Get all parent task IDs
        parent_tasks = task.previous_task()

        # Check if there are failed tasks among the ancestors and if we are
        # allowed to continue with less
        if [t for t in parent_tasks if t.status in ('failed', 'aborted')]:
            logging.error('Failed parent tasks detected. Unable to collect all output')

        # Check if the ancestors are all completed
        collected_output = []
        if all([t.status in ('completed', 'disabled') for t in parent_tasks]):
            msg = 'Task {0} ({1}): Output of {2} parent tasks available, continue'
            logging.info(msg.format(task.nid, task.key, len(parent_tasks)))
            
            # Collect output of previous tasks and apply data mapper and data
            # selection if needed
            for ptask in parent_tasks:
                output = ptask.get_output()
                edge = self.workflow.getedges((ptask.nid, task.nid))

                # Apply data mapping and selection by selecting only parameters
                # from the previous task that are defined in the edge
                # data_select list and data_mapping dictionary. In the latter
                # case the key/value mapping is performed.
                mapper = edge.get('data_mapping', {})
                select = edge.get('data_select', default=[])
                for key, value in mapper.items():
                    if not key in select:
                        select.append(key)
                    if value in select:
                        select.remove(value)

                new_dict = {mapper.get(k, k): '${0}.{1}'.format(ptask.nid, k) for k, v in output.items() if k in select}
                collected_output.append(new_dict)
        else:
            logging.info('Task {0} ({1}): Not all output available yet'.format(task.nid, task.key))
            return

        return concat_dict(collected_output)
    
    def _error_callback(self, failure, tid):
        """
        Process the output of a failed task and stage the next task to run
        if allowed

        :param failure: Twisted deferred error stack trace
        :type failure:  exception
        :param tid:     Task ID of failed task
        :type tid:      :py:int
        """

        task = self.workflow.getnodes(tid)

        failure_message = ""
        if isinstance(failure, Exception) or isinstance(failure, str):
            failure_message = str(failure)
        elif isinstance(failure, Failure):
            failure_message = failure.value
        else:
            failure.getErrorMessage()

        logging.error('Task {0} ({1}) crashed with error: {2}'.format(task.nid, task.key, failure_message))

        # Update task meta data
        task_meta = task.task_metadata
        task_meta.status.value = 'failed'
        task_meta.endedAtTime.set()

        # Update workflow metadata
        metadata = self.workflow.query_nodes(key='project_metadata')
        metadata.update_time.set()
        self.is_running = False

        return

    def _output_callback(self, output, tid):
        """
        Process the output of a task and stage the next task to run.

        A successful task is expected to return some output. If None it
        is considered to have failed by the workflow manager.

        :param output: output of the task
        :type output:  :py:dict
        :param tid:    Task ID
        :type tid:     :py:int
        """

        # Get the task
        task = self.get_task(tid)

        # Update project metadata
        metadata = self.workflow.query_nodes(key='project_metadata')
        metadata.update_time.set()

        # Update task metadata
        # If the task returned no output at all, fail it
        if output is None:
            logging.error('Task {0} ({1}) returned no output'.format(task.nid, task.key))
            task.status = 'failed'
        else:
            # Update the task output data only if not already 'completed'
            if task.status not in ('completed', 'failed'):
                task.set_output(output)
                task.status = 'completed'
                task.task_metadata.endedAtTime.set()

            logging.info('Task {0} ({1}), status: {2}'.format(task.nid, task.key, task.status))

        # Switch workdir if needed
        if metadata.project_dir.get():
            os.chdir(metadata.project_dir.get())

        # If the task is completed, go to next
        next_task_nids = []
        if task.status == 'completed':
            
            # Get next task(s) to run
            next_tasks = task.next_task()
            logging.info('{0} new tasks to run with output of {1} ({2})'.format(len(next_tasks), task.nid, task.key))

            for ntask in next_tasks:
                # Get output from all tasks connected to new task
                output = self._collect_input(ntask)
                if output is not None:
                    data = ntask.task_metadata.input_data.get(default={})
                    data.update(output)
                    ntask.set_input(**data)
                    next_task_nids.append(ntask.nid)

        # If the task failed, retry if allowed and reset status to "ready"
        if task.status == 'failed' and task.task_metadata.retry_count():
            task.task_metadata.retry_count.value -= 1
            task.status = 'ready'

            logging.warn('Task {0} ({1}) failed. Retry ({2} times left)'.format(task.nid, task.key,
                                                                                task.task_metadata.retry_count()))
            next_task_nids.append(task.nid)

        # If the active failed an no retry is allowed, save workflow and stop.
        if task.status == 'failed' and task.task_metadata.retry_count() == 0:
            logging.error('Task {0} ({1}) failed'.format(task.nid, task.key))
            if metadata.project_dir():
                self.save(os.path.join(metadata.project_dir(), 'workflow.jgf'))
            self.is_running = False
            return

        # If the task is completed but a breakpoint is defined, wait for the
        # breakpoint to be lifted
        if task.task_metadata.breakpoint():
            logging.info('Task {0} ({1}) finished but breakpoint is active'.format(task.nid, task.key))
            self.is_running = False
            return

        # No more new tasks
        if not next_task_nids:

            # Not finished but no active tasks anymore/breakpoint
            if not self.active_tasks and not self.is_completed:
                breakpoints = self.active_breakpoints
                if breakpoints:
                    logging.info('Active breakpoint: {0}'.format(', '.join([t.key for t in breakpoints])))
                self.is_running = False
                return

            # Finish of if there are no more tasks to run and all are completed
            if self.is_completed or self.has_failed:
                logging.info('finished workflow')
                self.is_running = False
                if not metadata.finish_time():
                    metadata.finish_time.set()
                if metadata.project_dir():
                    self.save(os.path.join(metadata.project_dir(), 'workflow.jgf'))
                return

        # Launch new tasks
        for tid in next_task_nids:
            self._run_task(tid)

    def _run_task(self, tid):
        """
        Run a task by task ID (tid)

        Handles the setup procedure for running a task using a dedicated Task
        runner. The output or errors of a task are handled by the
        `_output_callback` and `_error_callback` methods respectively.

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
        # Check if the task has a 'run_task' method.
        task = self.get_task(tid)
        metadata = self.workflow.query_nodes(key='project_metadata')

        # Do not continue if the task is active
        if task.is_active:
            logging.debug('Task {0} ({1}) already active'.format(task.nid, task.key))
            return

        # Run the task if status is 'ready'
        if task.status == 'ready':
            logging.info('Task {0} ({1}), status: preparing'.format(task.nid, task.key))

            # Check if there is 'input' defined
            if not task.has_input:

                # Check if previous task has output and use it as input
                # for the current
                parent = task.parent()
                if parent and 'output_data' in parent:
                    logging.info('Use output of parent task to tid {0} ({1})'.format(task.nid, parent.nid))

                    # Define reference to output
                    ref = dict([(key, '${0}.{1}'.format(parent.nid, key)) for key in parent.output_data])
                    task.set_input(**ref)

            # Do we need to store data to disk. Switch working directory
            if task.task_metadata.store_output():
                project_dir = metadata.project_dir()
                workdir = task.task_metadata.workdir
                workdir.set('value', os.path.join(project_dir, 'task-{0}-{1}'.format(task.nid, task.key.replace(' ', '_'))))
                workdir.makedirs()
                os.chdir(workdir.get())

            # Confirm again that the workflow is running
            self.is_running = True
            metadata.update_time.set()

            # Set workflow task meta-data
            task.status = 'running'
            task.task_metadata.startedAtTime.set()
            logging.info('Task {0} ({1}), status: {2}'.format(task.nid, task.key, task.status))
            task.run_task(self._output_callback, self._error_callback, task_runner=self.task_runner)

        # In all other cases, pass task data to default output callback
        # instructing it to not update the data but decide on the followup
        # workflow step to take.
        else:
            logging.info('Task {0} ({1}), status: {0}'.format(task.nid, task.key, task.status))
            self._output_callback({}, tid)

    @property
    def is_running(self):
        """
        Returns the global state of the workflow as running or not.

        :rtype: :py:bool
        """

        return self._is_running

    @is_running.setter
    def is_running(self, state):
        """
        Set the global state of the workflow as running or not.
        If the new state is 'False' first check if there are no other parallel
        active tasks.
        """

        if not state:
            state = len(self.active_tasks) >= 1
        self._is_running = state

    @property
    def is_completed(self):
        """
        Is the workflow completed successfully or not

        :rtype: :py:bool
        """

        return all([task.status in ('completed', 'disabled') for task in self.get_tasks()])

    @property
    def has_failed(self):
        """
        Did the workflow finish unsuccessfully?
        True if there are no more active tasks and at least one task has failed
        or was aborted
        """

        if not len(self.active_tasks) and any([task.status in ('failed', 'aborted') for task in self.get_tasks()]):
            return True

        return False

    @property
    def starttime(self):
        """
        Return the time stamp at which the workflow was last started

        :rtype: :py:int
        """

        metadata = self.workflow.query_nodes(key='project_metadata')
        return metadata.start_time.timestamp()

    @property
    def updatetime(self):
        """
        Return the time stamp at which the workflow was last updated

        :rtype: :py:int
        """

        metadata = self.workflow.query_nodes(key='project_metadata')
        return metadata.update_time.timestamp()

    @property
    def finishtime(self):
        """
        Return the time stamp at which the workflow finished or None
        if it has not yet finished

        :rtype: :py:int
        """

        if not self.is_running:
            metadata = self.workflow.query_nodes(key='project_metadata')
            return metadata.finish_time.timestamp()
        return None

    @property
    def runtime(self):
        """
        Return the total workflow runtime in seconds as the different between
        the start time and the finish time or last update time

        :rtype: :py:int
        """

        start = self.starttime or 0
        end = self.finishtime or self.updatetime

        # No update and finish time means the workflow was not started yet
        if not end:
            return 0

        return end - start

    @property
    def active_tasks(self):
        """
        Return all active tasks in the workflow

        :rtype: :py:list
        """

        return [task for task in self.get_tasks() if task.is_active]

    @property
    def failed_tasks(self):

        return [task for task in self.get_tasks() if task.status == 'failed']

    @property
    def active_breakpoints(self):
        """
        Return tasks with active breakpoint or None
        """

        return [task for task in self.get_tasks() if task.task_metadata.breakpoint.get(default=False)]

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
            logging.info('Unable to cancel workflow that is not running.')
            return

        # Get active task
        active_tasks = self.active_tasks
        logging.info('Cancel tasks: {0}'.format(', '.join([t.key for t in active_tasks])))

        for task in active_tasks:
            task.cancel()

        metadata = self.workflow.query_nodes(key='project_metadata')
        metadata.update_time.set()

        self.is_running = False

    def get_task(self, tid=None, key=None):
        """
        Return a task by task ID (graph nid) or task name (key).

        :param tid:       nid of task to return
        :type tid:        :py:int
        """

        if tid:
            task = self.workflow.getnodes(tid)
        elif key:
            task = self.workflow.query_nodes(key=key)
        else:
            raise WorkflowError('Search on task ID (tid) or task name (key). None defined')

        if task.empty():
            raise WorkflowError('Task with tid {0} not in workflow'.format(tid))
        if not task.get('format') == 'task':
            raise WorkflowError('Node with tid {0} is no task object'.format(tid))

        return task

    def step_breakpoint(self, tid):
        """
        Continue a workflow at a task that is paused by a breakpoint

        :param tid: workflow task ID with active breakpoint
        :type tid:  :py:int
        """

        task = self.get_task(tid)
        if not task.task_metadata.breakpoint.get(default=False):
            logging.warn('No active breakpoint set on task {0}'.format(task.key))
            return

        # Remove the breakpoint
        task.task_metadata.breakpoint.set('value', False)
        logging.info('Remove breakpoint on task {0} ({1})'.format(tid, task.key))

    def input(self, tid, **kwargs):
        """
        Define task input and configuration data
        """

        task = self.get_task(tid)
        task.set_input(**kwargs)

    def output(self, tid=None):
        """
        Get workflow output
        Returns the output associated to all terminal tasks (leaf nodes) of
        the workflow or of any intermediate tasks identified by the task ID

        :param tid: task ID to return output for
        :type tid:  :py:int
        """

        task = self.get_task(tid)

        output = {}
        if task.status == 'completed':
            output = task.get_output()

        return output

    def run(self, tid=None, validate=True):
        """
        Run a workflow specification

        Runs the workflow until finished, failed or a breakpoint is reached.
        A workflow is a rooted Directed Acyclic Graph (DAG) that is started
        from the root node. It can be started from any node relative to the
        root as long as its parent(s) are successfully completed.

        The workflow will be executed on a different thread allowing for
        interactivity with the workflow instance while the workflow is
        running.

        By default, the workflow specification will be validated using the
        `validate` method of the WorkflowSpec class.

        :param tid:      Start the workflow from task ID
        :type tid:       :py:int
        :param validate: Validate the workflow before running it
        :type validate:  :py:bool
        """

        # Start from workflow root by default
        tid = tid or self.workflow.root

        # Check if tid exists
        if tid not in self.workflow.nodes:
            raise WorkflowError('Task with tid {0} not in workflow'.format(tid))

        # Validate workflow before running?
        if validate:
            if not validate_workflow(self.workflow):
                return

        # Set is_running flag. Function as a thread-safe signal to indicate
        # that the workflow is running.
        metadata = self.workflow.query_nodes(key='project_metadata')
        if self.is_running:
            logging.warning('Workflow {0} is already running'.format(metadata.title()))
            return
        self.is_running = True

        # If there are steps that store results locally (store_output == True)
        # Create a project directory.
        if any(self.workflow.query_nodes(key="store_output").values()):
            if not metadata.project_dir():
                metadata.project_dir.set(metadata.node_value_tag, os.getcwd())
            logging.info('Project directory at: {0}'.format(metadata.project_dir.get()))
            metadata.project_dir.makedirs()

        logging.info('Running workflow: {0}, start task ID: {1}'.format(metadata.title(), tid))

        # Set workflow start time if not defined. Don't rerun to allow
        # continuation of unfinished workflow.
        if not metadata.start_time():
            metadata.start_time.set()

        # Spawn a thread
        self.workflow_thread = threading.Thread(target=self._run_task, args=[tid])
        self.workflow_thread.daemon = True
        self.workflow_thread.start()
