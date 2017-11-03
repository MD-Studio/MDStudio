# -*- coding: utf-8 -*-

# from lie_md.gromacs_gromit import gromit_cmd
from collections import defaultdict
from twisted.logger import Logger
import cerise_client.service as cc
import json
import os
from os.path import join
from time import sleep

# initialized twisted logger
logger = Logger()


def create_cerise_config(
        path_to_config, session, cwl_workflow):
    """
    Configuration to run MD jobs.
    """
    with open(path_to_config, 'r') as f:
        config = json.load(f)

    # Return None if key no in dict
    config = defaultdict(lambda: None, **config)
    config.update(session)

    # Set Workflow
    config['cwl_workflow'] = check_cwl_workflow(cwl_workflow)
    config['log'] = join(config['workdir'], 'cerise.log')

    return config


def call_cerise_gromacs(
        gromacs_config, cerise_config, cerise_collection):
    """
    Use cerise to run gromacs in a remote cluster, see:
    http://cerise-client.readthedocs.io/en/latest/

    :param gromacs_config: dict containing the gromacs parameters
    for the simulation.
    :param cerise_config: dict containing the settings to create
    and call a cerise-client process.
    :param cerise_collection: MongoDB collection to keep the information
    related to the Cerise services and jobs.
    """
    srv_data = retrieve_service_from_db(cerise_config, cerise_collection)

    if srv_data is None:
        srv = create_service(cerise_config, cerise_collection)
        job, srv_data = submit_new_job(
            srv, gromacs_config, cerise_config, cerise_collection)
    else:
        srv = restart_service(srv_data)
        job = srv.get_job_by_id(srv_data['job_id'])

    # Wait, extract and clean
    job = wait_for_job(job, cerise_config['log'])
    output = get_output(job, cerise_config)
    cleanup(srv, srv_data, cerise_collection)

    return output


def restart_service(srv_data):
    """
    use a dictionary to restart a service
    """
    logger.info(
        "There is already a service in the database, restarting it!")
    srv = cc.service_from_dict(srv_data)
    cc.start_managed_service(srv)

    return srv


def create_service(config, cerise_collection):
    """
    Create a Cerise service if one is not already running.
    """
    srv = cc.require_managed_service(
            config['docker_name'],
            config.get('port', 29593),
            config['docker_image'],
            config['username'],
            config['password'])
    logger.info("Created a new Cerise-client service")

    return srv


def submit_new_job(srv, gromacs_config, cerise_config, cerise_collection):
    """
    Create a new job and regiter it.
    """
    logger.info("Creating Cerise-client job")
    job = create_lie_job(srv, gromacs_config, cerise_config)

    # Associate a CWL workflow with the job
    job.set_workflow(cerise_config['cwl_workflow'])
    logger.info("CWL worflow is: {}".format(cerise_config['cwl_workflow']))

    # run the job in the remote
    msg = "Running the job in a remote machine using docker: {}".format(
        cerise_config['docker_image'])
    logger.info(msg)

    # submit the job and register it
    job.run()
    srv_data = register_srv_job(job, srv, cerise_collection)
    srv_data['username'] = cerise_config['username']

    return job, srv_data


def create_lie_job(srv, gromacs_config, cerise_config):
    """
    Create a Cerise job and set gromacs
    """
    job_name = 'job_{}'.format(cerise_config['task_id'])
    job = srv.create_job(job_name)

    # Copy gromacs input files
    job = copy_files_to_remote(job, gromacs_config)

    return set_input(job, gromacs_config)


def set_input(job, gromacs_config):
    """
    Set input variables
    """
    job.set_input('force_field', gromacs_config['forcefield'])
    # job.set_input('sim_time', gromacs_config['sim_time'])
    job.set_input('sim_time', 0.002)

    return job


def retrieve_service_from_db(config, cerise_collection):
    """
    Check if there is an alive service in the database.
    """
    query = {
        'username': config['username'], 'name': config['docker_name']}
    cursor = cerise_collection.find(query)
    if cursor.retrieved > 0:
        return cursor.next()
    else:
        return None


def register_srv_job(job, srv, cerise_collection):
    """
    Once the job is running in the queue system register
    it in the database.
    """
    while job.state == 'Waiting':
        sleep(2)

    # Save id of the current job in the set
    srv_data = cc.service_to_dict(srv)
    srv_data['job_id'] = job.id
    srv_data['job_state'] = job.state

    # Add srv_dict to database
    cerise_collection.insert_one(srv_data)
    logger.info("Added service to mongoDB")

    return srv_data


def wait_for_job(job, cerise_log):
    """
    Wait until job is done.
    """
    # Wait for job to finish
    while job.is_running():
        sleep(30)

    # Process output
    if job.state != 'Success':
        logger.error('There was an error: {}'.format(job.state))

    logger.info('Cerise log stored at: {}'.format(
        cerise_log))

    with open(cerise_log, 'w') as f:
        json.dump(job.log, f, indent=2)

    return job


def cleanup(srv, job, cerise_collection):
    """
    Clean up the job and the service.
    """
    logger.info("Shutting down Cerise-client service")
    srv.destroy_job(job)
    cc.destroy_managed_service(srv)

    # Remove job from DB
    remove_srv_job_from_db(srv, job, cerise_collection)


def remove_srv_job_from_db(srv, srv_data, cerise_collection):
    """
    Remove the service and job information from DB
    """
    job_id = srv_data['job_id']
    query = {'job_id': job_id}
    cerise_collection.delete_one(query)
    logger.info('Remove job: {} from database'.format(job_id))


def get_output(job, config):
    """
    retrieve output information from the job.
    """
    if job.state == 'Success':
        task_id = config['task_id']
        workdir = config['workdir']
        path = join(workdir, 'output_{}.trr'.format(task_id))
        job.outputs['trajectory'].save_as(path)

        return path

    else:
        return None


def copy_files_to_remote(job, gromacs_config):
    """
    Tell to Cerise which files to copy.
    """
    # copy_files to remote worker
    files = ['protein_pdb', 'protein_top', 'protein_itp',
             'ligand_pdb', 'ligand_top', 'ligand_itp']
    for name in files:
        job.add_input_file(name, gromacs_config[name])

    return job


def check_cwl_workflow(cwl_workflow):
    """
    Check whether a CWL worflow file exists and copy it to the workdir
    """
    if cwl_workflow is not None and os.path.isfile(cwl_workflow):
        return cwl_workflow
    else:
        root = os.path.dirname(__file__)
        return join(root, 'data/md_workflow.cwl')


def retrieve_energies(workdir):
    """
    """
    pass
