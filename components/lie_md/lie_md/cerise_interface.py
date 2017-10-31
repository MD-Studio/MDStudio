# -*- coding: utf-8 -*-

# from lie_md.gromacs_gromit import gromit_cmd
from twisted.logger import Logger
import cerise_client.service as cc
import json
import os
from os.path import join
from time import sleep

# initialized twisted logger
logger = Logger()


def create_cerise_config(
        path_to_config, workdir, session):
    """
    Configuration to run MD jobs.
    """
    with open(path_to_config, 'r') as f:
        config = json.load(f)

    config['workdir'] = workdir
    config['task_id'] = session["task_id"]
    config['service_dict'] = session.get('service_dict', None)
    config['jobs'] = set()
    config['log'] = join(workdir, 'cerise.log')

    return config


def call_cerise_gromacs(gromacs_config, cerise_config, cwl_workflow):
    """
    Use cerise to run gromacs in a remote cluster, see:
    http://cerise-client.readthedocs.io/en/latest/
    """
    logger.info("Creating a Cerise-client service")
    srv, cerise_config = create_service(cerise_config)

    # Start service
    cc.start_managed_service(srv)

    # Create jobs
    logger.info("Creating Cerise-client job")
    job = create_lie_job(srv, gromacs_config, cerise_config, cwl_workflow)

    # Set Workflow
    cwl_workflow = check_cwl_workflow(cwl_workflow)
    job.set_workflow(cwl_workflow)
    logger.info("CWL worflow is: {}".format(cwl_workflow))

    # run the job in the remote
    logger.info("Running the job in a remote machine")
    job.run()

    # Wait for the job to finish
    job, cerise_config = wait_for_job(job, cerise_config)

    output = get_output(job, cerise_config)

    cleanup(srv, job, cerise_config)

    return output, cerise_config


def cleanup(srv, job, cerise_config):
    """
    Clean up the job and the service
    """
    logger.info("Shutting down Cerise-client service")
    srv.destroy_job(job)
    cc.destroy_managed_service(srv)


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


def wait_for_job(job, cerise_config):
    """
    Wait until job is done.
    """
    # Waiting for job to finish
    while job.state == 'Waiting':
        sleep(5)

    # Save id of the current job in the set
    cerise_config['jobs'].add(job.id)

    # Wait for job to finish
    while job.is_running():
        sleep(10)

    # Process output
    if job.state != 'Success':
        logger.error('There was an error: {}'.format(job.state))

    logger.info('Cerise log stored at: {}'.format(
        cerise_config['log']))

    with open(cerise_config['log'], 'w') as f:
        json.dump(job.log, f)

    return job, cerise_config


def create_service(config):
    """
    Create a Cerise service if one is not already running.
    """
    srv_data = config.get('service_dict', None)
    if srv_data is not None:
        srv = cc.service_from_dict(srv_data)
    else:
        srv = cc.require_managed_service(
            config['docker_name'],
            config.get('port', 29593),
            config['docker_image'],
            config['user_name'],
            config['password'])

        # Update config
        config['service_dict'] = cc.service_to_dict(srv)

    return srv, config


def create_lie_job(srv, gromacs_config, cerise_config, cwl_workflow):
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
    job.set_input('sim_time', gromacs_config['sim_time'])

    return job


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
