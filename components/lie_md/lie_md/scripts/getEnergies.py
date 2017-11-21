'''
Tool to gather ensemble energies and per-residue decomposed energies from
gromacs md files (edr and trr for decomposition)
The program execute gromacs commands from inside

examples of execution:
1. To gather energies from edr : python getEnergies.py -gmxrc /opt/gromacs-4.6.7/bin/GMXRC -ene -o energy.dat

2. to obtained per-residue decompose contributes: python getEnergies.py -gmxrc /opt/gromacs-4.6.7/bin/GMXRC -dec -o energydec.dat -res "416,417,418,419,420,421,422,423"

For decomposition, configuration as in mdpName='md-prod-out.mdp' is used.
Rerun is performed for the trajectory: ext='trr',pref='*?MD*'
template index file is: ext='ndx',pref='*?sol'
gro file for getting aton umber for residue is: ext='gro',pref='*?sol'
top file is: 'top',pref='*?sol'
'''

import argparse
import collections
import fnmatch
import logging
import numpy as np
import os
import sys
from panedr import edr_to_df
from subprocess import (PIPE, Popen)


def main(args):

    # Create gromacs environment
    gmxEnv = getGMXEnv(args.gmxrc) if args.gmxrc is not None else os.environ

    # Full energy gathering
    if args.energy and args.decompose:
        msg = 'Make a decision: decomposition (-dec) or ensemble energy gathering (-ene)!'
        log_and_quit(msg)

    if args.energy:
        process_energies(args.dataDir, args.outName)

    # Per-residue energy decomposition
    if args.decompose:
        decompose(args, gmxEnv)
    logging.info('SUCCESSFUL COMPLETION OF THE PROGRAM')


def process_energies(dataDir, outName):
    """
    Read and format energies.
    """
    path = findFile(dataDir, ext='edr', pref='*energy*')
    if path is None:
        msg = 'TERMINATED. Program {} not found.'.format(path)
        log_and_quit(msg)
    else:
        frames = get_energy(path)
        labs2print = [
            'Time', 'Potential', 'Kinetic En.', 'Temperature', 'ele', 'vdw',
            'Ligand-Ligenv-ele', 'Ligand-Ligenv-vdw']
        writeOut(frames, outName, labs2print)


def get_energy(path, listRes=['Ligand']):
    """
    Read Energies from a .edr file and
    use the `panedr` library to parse it.

    :params path:  Path to the edr file.
    """
    df = edr_to_df(path)
    # Electrostatic Energy
    df['ele'] = sum_available_columns(
        df, ['Coulomb-14', 'Coulomb (SR)', 'Coulomb (LR)', 'Coul. recip.'])

    # Van der Waals terms
    df['vdw'] = sum_available_columns(
        df, ['LJ-14', 'LJ (SR)', 'LJ (LR)'])

    return extract_ligand_info(df, listRes)


def extract_ligand_info(df, listRes):
    """
    Get the Ligand information.
    """
    for res in listRes:
        names = get_residue_from_columns(res, df.columns)
        df = compute_terms_per_residue(df, names)

    return df


def get_residue_from_columns(name, columns):
    """
    Extract the ligand terms from the column names.

    :param name: Name of the residue
    :param columns: name of the columns in the dataframe
    :return: dictionary containing the residue's names as
           keys and electrostatic and vdw names as values.
    """
    names = collections.defaultdict(list)
    for c in filter(lambda x: name in x, columns):
        v, k = c.split(':')
        names[k].append(v)

    # Sort the list
    for xs in names.values():
        xs.sort()

    return names


def compute_terms_per_residue(df, names):
    """
    Split the names in the electrostatic and van der Waals terms
    and compute the electronic and VDW terms for each one of
    the residue terms specified in the `names` dictionary.

    :param df: Pandas dataframe
    :param names: dictionary of the names use in the dataframe.
    :return: updated dataframe
    """
    for key, vals in names.items():
        sufix_elec = vals[:2]
        sufix_vdw = vals[2:]
        names_elec = ['{}:{}'.format(x, key) for x in sufix_elec]
        names_vdw = ['{}:{}'.format(x, key) for x in sufix_vdw]
        res_elec = '{}-ele'.format(key)
        res_vdw = '{}-vdw'.format(key)

        df[res_elec] = df[names_elec].sum(axis=1)
        df[res_vdw] = df[names_vdw].sum(axis=1)

    return df


def sum_available_columns(df, labels):
    """
    Sum columns if they are in the dataframe
    """
    cols = [x for x in labels if x in df.columns]
    return df[cols].sum(axis=1)


def writeOut(frames, output_file, columns):
    """
    write columns as a table
    """
    with open(output_file, 'w') as f:
        f.write(frames[columns].to_string(index=False))


def decompose(args, gmxEnv):
    """
    Make a decomposition of the energy into its residue components
    """
    if args.resList is None:
        msg = 'TERMINATED. List of residues not provided.'
        log_and_quit(msg)

    if not all(availProg(cmd, gmxEnv)
               for cmd in ['grompp', 'mdrun', 'gmxdump']):
        msg = 'TERMINATED. Programs required for decomposition not found.'
        log_and_quit(msg)

    # parse MD mdp
    mdpIn = findFile(args.dataDir, ext='mdp', pref='*')
    mdpDict = parseMdp(mdpIn)

    # create decomposition mdp, ndx and run rerun
    gro = findFile(args.dataDir, ext='gro', pref='*sol')
    ndx = findFile(args.dataDir, ext='ndx', pref='*sol')
    trr = findFile(args.dataDir, ext='trr', pref='*MD*')
    top = findFile(args.dataDir, ext='top', pref='*sol')
    prefix_result = decomp(gmxEnv, mdpDict, args.resList, ndx, gro, top, trr)
    if prefix_result is None:
        msg = 'Decomposition fails!'
        log_and_quit(msg)

    energy_analysis(prefix_result)


def energy_analysis(prefix):
    """Analysis of energy decomposition file after rerun"""
    path = findFile(args.dataDir, ext='edr',  prefix=prefix)
    logging.info(
        "Extracting decomposed energies from {} file".format(path))
    df = get_energy(path)

    write_decomposition_ouput(df, args.outName, args.resList)


def decomp(
         gmxEnv, mdpDict, res_array, ndx_file, gro_file, top_file, trr_file,
        ligGroup='Ligand', outPref='decompose', suff4ndx='sol'):
    """ """

    mdp_file = create_new_mdp_file(mdpDict, res_array, ligGroup, outPref)

    # create a dictionary with the index of the atoms that belong
    # to a given residue
    dict_residues = create_residue_dict(gro_file)

    # create new ndx file:
    new_ndx_file = create_new_ndx_file(dict_residues, ndx_file)

    # run rerun
    cmd = ['grompp', '-f', mdp_file, '-c', gro_file, '-p',
           top_file, '-n', new_ndx_file, '-o', outTpr]
    
    success = executeProg(cmd, gmxEnv)
    if not success:
        msg = 'Something went wrong in the creation of the tpr file  for decomposition analysis'
        return (False, msg)

    outTpr='%s.tpr'%outPref

    cmd = ['mdrun', '-s', outTpr, '-rerun', trr, '-deffnm', outPref]
    success = executeProg(cmd, gmxEnv)
    if not success:
        msg = 'Something went wrong in the rerun decomposition analysis'
        return False, msg

    return outPref


def create_residue_dict(gro_file, res_array):
    """
    Read residues from the `gro_file` and create
    a dict that map the the residues listed in `res_array`
    with their correspoding atoms.
    """
    dict_residues = {}
    with open(gro_file, 'r') as inGro:
        for nl, line in enumerate(inGro):
            if nl > 2:
                line_sp = [int(line[0:5]), line[5:10].rstrip().lstrip(), line[10:15].rstrip().lstrip(), int(line[15:20]), line[20:28], line[28:36], line[36:44]]
                if line_sp[1] == 'SOL':
                    break
                if line_sp[0] in res_array:
                    if line_sp[0] not in dict_residues:
                        dict_residues[line_sp[0]] = []
                    dict_residues[line_sp[0]].append(line_sp[3])

    return dict_residues


def create_new_ndx_file(dict_residues, ndx_file):
    """"""
    new_ndx_file ='decomposition.ndx'
    with open(outNdx, 'w') as outFile:
        with open(ndx, 'r') as inNdx:
            for line in inNdx:
                outFile.write(line)
        for res in dict_residues:
            outFile.write('[ %d ]\n'%res)
            for atm in dict_residues[res]:
                outFile.write('%7d'%atm)
            outFile.write('\n')

    return new_ndx_file


def create_new_mdp_file(mdpDict, res_array, ligGroup):
    """ Crate a new input mdp file """

    listkeys = [
        'include', 'define', 'cutoff-scheme', 'ns-type', 'pbc',
        'periodic-molecules', 'rlist', 'rlistlong', 'nstcalclr',
        'coulombtype', 'coulomb-modifier', 'rcoulomb-switch', 'rcoulomb',
        'epsilon-r', 'epsilon-rf', 'vdw-type', 'vdw-modifier', 'rvdw-switch',
        'rvdw', 'DispCorr', 'table-extension', 'energygrp-table',
        'fourierspacing', 'fourier-nx', 'fourier-ny', 'fourier-nz',
        'pme-order', 'ewald-rtol', 'ewald-geometry', 'epsilon-surface',
        'optimize-fft', 'implicit-solvent', 'QMMM', 'constraints',
        'constraint-algorithm', 'continuation', 'Shake-SOR', 'shake-tol',
        'lincsorder', 'lincs-iter', 'lincs-warnangle', 'morse',
        'nwall', 'wall-type', 'wall-r-linpot', 'wall-atomtype', 'wall-density',
        'wall-ewald-zfac', 'pull', 'rotation', 'disre', 'orire',
        'free-energy', 'simulated-tempering']

    newKeys = {
        'nstxout': '0', 'nstvout': '0', 'nstfout': '0', 'nstlog': '0',
        'nstcalcenergy': '1', 'nstenergy': '1', 'nstxtcout': '0',
        'xtc-precision': '0', 'xtc-grps': '', 'nstlist': '1'}

    # the [1:-1] removes the [ ] from the beginning and the end
    str_residues = np.array_str(res_array)[1:-1]
    energygrps = '{}{}'.format(ligGroup, str_residues)

    newKeys['energygrps'] = energygrps

    new_input = ''
    fmt = "{:15s} = {}\n"
    for mdpKey in newKeys:
        new_input += fmt.format(mdpKey, newKeys[mdpKey])

    for mdpKey in (x for x in listkeys if x in mdpDict):
        new_input += fmt.format(mdpKey, mdpDict[mdpKey])

    mdp_file = "decomposition.mdp"
    with open(mdp_file, 'w') as f:
        f.write(new_input)

    return mdp_file


def write_decomposition_ouput(listFrames, outName, resList):
    """ Write results for decomposition """
    hs1 = ['time', 'Potential', 'ele', 'vdw']
    hs2 = ['Ligand-{}-vdw'.format(x) for x in resList]
    hs3 = ['Ligand-rest-vdw']
    hs4 = ['Ligand-{}-ele'.format(x) for x in resList]
    hs5 = ['Ligand-rest-ele']

    labs2print = hs1 + hs2 + hs3 + hs4 + hs5
    writeOut(listFrames, outName, labs2print)


def parseResidues(xs):
    """ return an array of the residues index """
    return np.array(xs.split(','), dtype=np.int32)


def parseMdp(mdpIn):
    """ Read the mdp input file"""
    with open(mdpIn, 'r') as inFile:
        xss = inFile.readlines()

    rs = filter(lambda line: not line.startswith(';') and '=' in line, xss)
    key_vals = [check_lenght(x.split()[::2]) for x in rs]

    return dict(key_vals)


def check_lenght(xs):
    """ transform list to tuples fixing the lenght """
    if len(xs) == 1:
        return tuple(xs[0], None)
    else:
        return tuple(xs)


def log_and_quit(msg):
    """
    Log a message and quit the program
    """
    logging.error(msg)
    sys.exit(-1)


def availProg(prog, myEnv):
    """ Check if a program is available """
    cmds = (os.path.join(path, prog)
            for path in myEnv["PATH"].split(os.pathsep))

    return any(os.path.isfile(cmd) and os.access(cmd, os.X_OK)
               for cmd in cmds)


def findFile(workdir, ext=None, pref=''):
    """ Check whether a file exists"""
    print(workdir, ext, pref)
    rs = fnmatch.filter(os.listdir(workdir), "{}.{}".format(pref, ext))
    if rs:
        return os.path.join(workdir, rs[0])

    else:
        logging.error(
            "file not Found with prefix: {} and ext: {}".format(pref, ext))
        return None


def getGMXEnv(gmxrc):
    """ Use Gromacs environment """
    command = ['bash', '-c', 'source {} && env'.format(gmxrc)]
    rs = call_subprocess(command)

    return {key: val for key, val in map(process_line, rs)}


def process_line(line):
    """ Split a Line in key, value pairs """
    key, value = line.partition("=")[::2]
    return key, value.rstrip()


def call_subprocess(cmd,  env=None):
    """
    Execute shell command and wait for the results
    """
    try:
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        rs = p.communicate()
        err = rs[1]
        if err:
            logging.error("Subprocess fails with error: {}".format(err))
        else:
            return rs[0]

    except Exception as e:
        log_and_quit("Subprocess fails with error: {}".format(e))


if __name__ == "__main__":
    logging.basicConfig(level='INFO')
    parser = argparse.ArgumentParser(
        description='Dock sdf file into protein conformation')

    parser.add_argument(
        '-gmxrc', required=False, dest='gmxrc',
        help='GMXRC file for environment loading')
    parser.add_argument(
        '-d', '--dir', required=False, dest='dataDir',
        help='directory with MD files to process', default=os.getcwd())
    parser.add_argument(
        '-dec', '--decompose', dest='decompose',
        help='perform residue decomposition analysis', action='store_true')
    parser.add_argument(
        '-ene', '--energy', dest='energy', help='gather total energy',
        action='store_true')
    parser.add_argument(
        '-res', '--residues', required=False, dest='resList',
        help='list of residue for which to decompose interaction energies (e.g. "1,2,3")',
        type=parseResidues)
    parser.add_argument(
        '-o', '--output', dest='outName', required=True)

    args = parser.parse_args()

    main(args)
