# -*- coding: utf-8 -*-

# from lie_md.gromacs_gromit import gromit_cmd
from collections import defaultdict
from twisted.logger import Logger
import cerise_client.service as cc
import hashlib
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
        gromacs_config, cerise_config, cerise_db):
    """
    Use cerise to run gromacs in a remote cluster, see:
    http://cerise-client.readthedocs.io/en/latest/

    :param gromacs_config: dict containing the gromacs parameters
    for the simulation.
    :param cerise_config: dict containing the settings to create
    and call a cerise-client process.
    :param cerise_db: MongoDB collection to keep the information
    related to the Cerise services and jobs.
    """
    srv_data = retrieve_service_from_db(
        cerise_config, gromacs_config['ligand_pdb'], cerise_db)

    if srv_data is None:
        srv_data = create_new_srv_job(
            gromacs_config, cerise_config, cerise_db)

    # is the job still running?
    elif srv_data['job_state'] == 'Running':
        restart_srv_job(srv_data)

    # Simulation information including cerise data
    sim_dict = extract_simulation_info(
        srv_data, cerise_config, cerise_db)

    # Shutdown Service if there are no other jobs running
    try_to_close_service(srv_data, cerise_db)

    return sim_dict


def retrieve_service_from_db(config, ligand_pdb, cerise_db):
    """
    Check if there is an alive service in the database.
    """
    query = {
        'ligand_md5': compute_md5(ligand_pdb),
        'name': config['docker_name']}

    return cerise_db.find_one(query)


def create_new_srv_job(gromacs_config, cerise_config, cerise_db):
    """
    Create a new service if one is not already running
    and initialize a job
    """
    srv = create_service(cerise_config)
    srv_data = submit_new_job(
        srv, gromacs_config, cerise_config, cerise_db)

    return srv_data


def create_service(config):
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


def submit_new_job(srv, gromacs_config, cerise_config, cerise_db):
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

    # Store data in the DB
    srv_data = collect_srv_data(
        job.id, cc.service_to_dict(srv), gromacs_config,
        cerise_config['username'])

    return register_srv_job(
        job, srv_data, cerise_db)


def restart_srv_job(srv_data):
    """ use a dictionary to restart a service """
    srv = cc.service_from_dict(srv_data)
    cc.start_managed_service(srv)

    job = srv.get_job_by_id(srv_data['job_id'])

    logger.info("Job {} already running".format(job.id))


def wait_extract_clean(job, srv, cerise_config, cerise_db):
    """
    Wait for the job to finish, extract the output and cleanup.
    """
    job = wait_for_job(job, cerise_config['log'])
    output = get_output(job, cerise_config)
    cleanup(job, srv, cerise_db)

    return output


def extract_simulation_info(
        srv_data, cerise_config, cerise_db):
    """
    Wait for a job to finish if the job is already done
    return the information retrieve from the db.
    """
    logger.info("Extracting output from: {}".format(
        cerise_config['workdir']))

    if not is_output_available(srv_data):
        srv = cc.service_from_dict(srv_data)
        job = srv.get_job_by_id(srv_data['job_id'])
        output = wait_extract_clean(
            job, srv, cerise_config, cerise_db)

        # Update data in the repo
        srv_data.update(output)
        srv_data['job_state'] = job.state
        update_srv_info_at_db(srv_data, cerise_db)

    # remove mongoDB object id
    srv_data.pop('_id', None)

    return srv_data


def is_output_available(srv_data):
    """
    Check if there are some output files.
    """
    outputs = ['gromiterr', 'gromitout', 'gromacslog', 'trajectory']
    return any(x in srv_data for x in outputs)


def update_srv_info_at_db(srv_data, cerise_db):
    """
    Update the service-job data store in the db
    """
    query = {'ligand_md5': srv_data['ligand_md5']}
    cerise_db.update_one(query, {"$set": srv_data})


def collect_srv_data(
        job_id, srv_data, gromacs_config, username):
    """
    Add all the relevant information for the job and
    service to the service dictionary
    """
    # Save id of the current job in the dict
    srv_data['job_id'] = job_id

    # create a unique ID for the ligand
    ligand_pdb = gromacs_config['ligand_pdb']

    srv_data['ligand_md5'] = compute_md5(ligand_pdb)
    srv_data['username'] = username

    return srv_data


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
    job.set_input('sim_time', gromacs_config['sim_time'])

    return job


def register_srv_job(job, srv_data, cerise_db):
    """
    Once the job is running in the queue system register
    it in the database.
    """
    while job.state == 'Waiting':
        sleep(2)

    # Add srv_dict to database
    srv_data['job_state'] = 'Running'
    cerise_db.insert_one(srv_data)
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


def cleanup(job, srv, cerise_db, remove_job_from_db=False):
    """
    Clean up the job and the service.
    """
    logger.info("removing job: {} from Cerise-client".format(job.id))
    srv.destroy_job(job)

    # Remove job from DB
    if remove_job_from_db:
        remove_srv_job_from_db(srv, job.id, cerise_db)


def remove_srv_job_from_db(srv, job_id, cerise_db):
    """
    Remove the service and job information from DB
    """
    query = {'job_id': job_id}
    cerise_db.delete_one(query)
    logger.info('Removed job: {} from database'.format(job_id))


def try_to_close_service(srv_data, cerise_db):
    """
    Close service it There are no more jobs and
    the service is still running.
    """
    try:
        srv = cc.service_from_dict(srv_data)

        # Search for other running jobs
        query = {'username': srv_data['username'], 'job_state': 'Running'}
        counts = cerise_db.find(query).count()

        if counts == 0:
            logger.info("Shutting down Cerise-client service")
            cc.stop_managed_service(srv)
            cc.destroy_managed_service(srv)

    except cc.errors.ServiceNotFound:
        logger.info("There is not Cerise Service running")
        pass


def get_output(job, config):
    """
    retrieve output information from the job.
    """
    output_dict = {
        'gromitout': 'gromit_{}.out', 'gromiterr': 'gromit_{}.err',
        'gromacslog': 'gromacs_{}.log', 'trajectory': 'traj_{}.trr',
        'energy': 'energy_{}.edr'}

    if job.state == 'Success':
        return {
            key: copy_output_from_remote(val, config, output_dict[key])
            for key, val in job.outputs.items()}

    else:
        return None


def copy_output_from_remote(val, config, fmt):
    """
    Copy output files to the localhost.
    """
    task_id = config['task_id']
    workdir = config['workdir']

    path = join(workdir, fmt.format(task_id))
    val.save_as(path)

    return path


def compute_md5(file_name):
    """
    Compute the md5 for a given file name
    """
    with open(file_name) as f:
        xs = f.read()

    return hashlib.md5(xs).hexdigest()


def copy_files_to_remote(job, gromacs_config):
    """
    Tell to Cerise which files to copy.
    """
    # copy_files to remote worker
    files = ['protein_pdb', 'protein_top', 'protein_itp',
             'ligand_pdb', 'ligand_top', 'ligand_itp',
             'include_itp']
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
