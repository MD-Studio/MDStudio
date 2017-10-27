# -*- coding: utf-8 -*-

# from lie_md.gromacs_gromit import gromit_cmd
from twisted.logger import Logger
import cerise_client.service as cc
import json

logger = Logger()


def create_cerise_config(path_to_config, workdir, session):
    """
    Configuration to run MD jobs.
    """
    with open(path_to_config, 'r') as f:
        config = json.load(f)

    config['workdir'] = workdir
    config['task_id'] = session["task_id"]
    config['service_dict'] = session.get('service_dict', None)

    return config


def call_cerise_gromacs(gromacs_config, cerise_config):
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
    job = create_lie_job(srv, gromacs_config, cerise_config)

    # run the job in the remote
    logger.info("Running the job in a remote machine")
    run_job(job, srv, cerise_config)

    logger.info("Shutting down Cerise-client service")
    cc.stop_managed_service(srv)


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


def create_lie_job(srv, gromacs_config, cerise_config):
    """
    Create a Cerise job and set gromacs
    """
    job_name = 'job_{}'.format(cerise_config['task_id'])
    job = srv.create_job(job_name)

    # copy_files to remote worker
    files = ['protein_pdb', 'ligand_pdb', 'ligand_itp']
    for name in files:
        job.add_input_file(name, gromacs_config[name])

    return job


def run_job(job, srv, cerise_config):
    pass


def copy_files_to_remote(srv, gromacs_config):
    """
    Tell to Cerise which files to copy.
    """
    pass


def retrieve_energies(workdir):
    """
    """
    pass
