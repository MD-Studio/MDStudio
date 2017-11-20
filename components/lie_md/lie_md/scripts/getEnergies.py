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

import os
import sys
import subprocess as sp
import argparse
import logging
import re
from subprocess import (PIPE, Popen)
from tempfile import NamedTemporaryFile
from twisted.logger import Logger


logger = Logger()

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


def getEne(fileEne,, listRes=['Ligand']):
    pass

def parseResidues(strinput):
  indexmol = []
  tempindexmol = strinput.split(',')
  for item in tempindexmol:
    if len(item.split('-'))==1:
      indexmol.append(int(item))
    elif len(item.split('-'))==2:
      indexmol+=range(int(item.split('-')[0]),int(item.split('-')[1])+1)
    else:
      raise Exception("Invalid list,%i"%len(item.split('-')))
  indexmol=sorted(set(indexmol))

  return indexmol


def writeOut(card,oene,cols):

    output=open(oene,"w")

    lineOut='%7s' % ('"%s"'%"FRAME")
    for colName in cols:
        if len(colName) <= 9:
            lineOut+='%12s'%('"%s"'%colName)
        else:
            lineOut+='%*s'%(len(colName)+3,'"%s"'%colName)
        

    output.write("%s\n"%lineOut)

    for nfr,frame in enumerate(card):
        lineOut="%7i"%nfr
        for colName in cols:
            if len(colName) <= 12:
                lineOut+="%12.2f"%frame[colName]
            else:
                lineOut+="%*.2f"%(len(colName)+1,frame[colName])
        output.write("%s\n"%lineOut)

    output.close()

   
def parseMdp(mdpIn):
    mdpDict={}
    with open(mdpIn,'r') as inFile:
        for line in inFile:
            line=line.rstrip().lstrip()
            if not line.startswith(';'):
                if len(line)>0:
                    line_sp=re.split(r'\s{0,}=\s{0,}',line.rstrip().lstrip())  # split
                    mdpDict[line_sp[0]]=line_sp[1]

    return mdpDict


def executeProg(cmd,myEnv):
    try:
        proc=sp.Popen(cmd,stdout=sp.PIPE,stderr=sp.PIPE, env=myEnv)
        while True:
            outLine = proc.stdout.readline()
            errLine= proc.stderr.readline()
            if outLine == '' and errLine == '' and proc.poll() != None:
                break
            logger.debug("OUT: %s"%outLine)
            logger.debug("ERR: %s"%errLine)
            sys.stdout.flush()
            sys.stderr.flush()
    except Exception, e:
        logger.error(e)
        return False
    return True


def decomp(
        mdpDict, resList, ndx, gro, top, trr, gmxEnv,
        ligGroup='Ligand', outPref='decompose', suff4ndx='sol'):

    newKeys = {
        'nstxout': '0', 'nstvout': '0', 'nstfout': '0', 'nstlog': '0',
        'nstcalcenergy': '1', 'nstenergy': '1', 'nstxtcout': '0',
        'xtc-precision': '0', 'xtc-grps': '', 'nstlist': '1'}

    newKeys['energygrps'] = ligGroup

    for res in resList:
        newKeys['energygrps'] += ' {}'.format(res)

    outMdp = "{}.mdp".format(outPref)
    with open(outMdp, 'w') as outFile:
        for mdpKey in newKeys:
            outFile.write("%15s = %s\n"%(mdpKey,newKeys[mdpKey]))

        for mdpKey in listkeys:
            if mdpKey in mdpDict:
                outFile.write("%15s = %s\n"%(mdpKey,mdpDict[mdpKey]))

    ### prepare index file
    ## 1. create a dictionary with for each residue, its atom numbers
    resAtoms={}
    with open(gro,'r') as inGro:
        for nl, line in enumerate(inGro):
            if nl > 2:
                line_sp=[int(line[0:5]), line[5:10].rstrip().lstrip(), line[10:15].rstrip().lstrip(), int(line[15:20]), line[20:28], line[28:36], line[36:44]]
                if line_sp[1]=='SOL':
                    break
                if line_sp[0] in resList:
                    if line_sp[0] not in resAtoms:
                        resAtoms[line_sp[0]]=[]
                    resAtoms[line_sp[0]].append(line_sp[3])

    ## 2. create new ndx file:
    outNdx='%s.ndx'%outPref
    with open(outNdx, 'w') as outFile:
        with open(ndx, 'r') as inNdx:
            for line in inNdx:
                outFile.write(line)
        for res in resAtoms:
            outFile.write('[ %d ]\n'%res)
            for atm in resAtoms[res]:
                outFile.write('%7d'%atm)
            outFile.write('\n')

    outTpr='%s.tpr'%outPref


    # run rerun
    cmd = ['grompp', '-f', outMdp, '-c', gro, '-p', top, '-n', outNdx, '-o', outTpr]
    success = executeProg(cmd, gmxEnv)
    if not success:
        msg = 'Something went wrong in the creation of the tpr file  for decomposition analysis'
        return (False, msg)

    cmd = ['mdrun', '-s', outTpr, '-rerun', trr, '-deffnm', outPref]
    success = executeProg(cmd, gmxEnv)
    if not success:
        msg = 'Something went wrong in the rerun decomposition analysis'
        return False, msg

    return (True, outPref)


def process_energies(outName):
    """
    Read and format energies
    """
    path = findFile(dataDir, ext='edr', pref='*?MD*')
    if path is not None:
        frames = getEne(path)
        labs2print = [
            'time', 'Potential', 'Kinetic En.', 'Temperature', 'ele', 'vdw',
            'Ligand-Ligenv-ele', 'Ligand-Ligenv-vdw']
    writeOut(frames, outName, labs2print)
    else:
        logger.error('TERMINATED. Program %s not found.'.format(cmd))
        sys.exit(1)


def decompose(args):
    """
    Make a decomposition
    """
    if args.resList is None:
        logger.error('TERMINATED. List of residues not provided.')
        sys.exit(1)

    if not all(availProg(cmd, gmxEnv)
               for cmd in ['grompp', 'mdrun', 'gmxdump']):
        logger.error('TERMINATED. Programs required for decomposition not found.')
        sys.exit(1)

    resList = parseResidues(args.resList)
    mdpName = 'md-prod-out.mdp'
    mdpIn = os.path.join(dataDir, mdpName)
    # parse MD mdp
    mdpDict = parseMdp(mdpIn)
    # create decomposition mdp, ndx and run rerun
    gro = findFile(dataDir, ext='gro', pref='*?sol')
    ndx = findFile(dataDir, ext='ndx', pref='*?sol')
    trr = findFile(dataDir, ext='trr', pref='*?MD*')
    top = findFile(dataDir, ext='top', pref='*?sol')
    results = decomp(mdpDict, resList, ndx, gro, top, trr, gmxEnv)
    if results is None:
        logger.error(results)
        sys.exit(1)
    # Analysis of energy decomposition file after rerun
    success, results = findFile(dataDir, ext='edr', pref=results)
    if success:
        logger.debug(
            "Extracting decomposed energies from %s file".format(results))
        listFrames = getEne(results, gmxEnv)
    else:
        logger.error(results)
        sys.exit(1)

    write_decomposition_ouput(listFrames, outName, resList)


def write_decomposition_ouput(listFrames, outName, resList):
    """ Write results for decomposition """
    hs1 = ['time', 'Potential', 'ele', 'vdw']
    hs2 = ['Ligand-{}-vdw'.format(x) for x in resList]
    hs3 = ['Ligand-rest-vdw']
    hs4 = ['Ligand-{}-ele'.format(x) for x in resList]
    hs5 = ['Ligand-rest-ele']

    labs2print = hs1 + hs2 + hs3 + hs4 + hs5
    writeOut(listFrames, outName, labs2print)


def main(args):
    # Data dir definition
    dataDir = args.dataDir if args.dataDir is not None else os.getcwd()

    # output file
    outName = args.outName

    # Create gromacs environment
    gmxEnv = getGMXEnv(args.gmxrc) if args.gmxrc is not None else os.environ

    # Full energy gathering
    if args.energy and args.decompose:
        msg = 'Make a decision: decomposition (-dec) or ensemble energy gathering (-ene)!'
        logger.error(msg)
        sys.exit(-1)

    if args.energy:
        process_energies(gmxEnv, outName)

    # Per-residue energy decomposition
    if args.decompose:
        decompose(args)
    logger.info('SUCCESSFUL COMPLETION OF THE PROGRAM')


def availProg(prog, myEnv):
    """ Check if a program is available """
    cmds = (os.path.join(path, prog)
            for path in myEnv["PATH"].split(os.pathsep))

    return any(os.path.isfile(cmd) and os.access(cmd, os.X_OK)
               for cmd in comds)


def findFile(wdir, ext=None, pref=''):
    """ Check whether a file exists"""
    path = os.path.join(wdir, "{}.{}".format(pref, ext))

    if os.path.isfile(path):
        return path
    else:
        logger.error("{} file not Found")
        return None

def getGMXEnv(gmxrc):
    """ Use Gromacs environment """
    command = ['bash', '-c', 'source {} && env'.format(gmxrc)]
    rs = call_subprocess(command)

    return {key: val for key, val in map(process_line, rs)}


def process_line():
    """ Split a Line in key, value pairs """
    key, value = line.partition("=")[::2]
    return key, value.rstrip()


def call_subprocess(cmd):
    """
    Execute shell command and wait for the results
    """
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    rs = p.communicate()
    err = rs[1]
    if err:
        raise RuntimeError("Submission Errors: {}".format(err))
    else:
        return rs[0]


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Dock sdf file into protein conformation')

    parser.add_argument(
        '-gmxrc', required=False, dest='gmxrc',
        help='GMXRC file for environment loading')
    parser.add_argument(
        '-d', '--dir', required=False, dest='dataDir',
        help='directory with MD files to process', default=None)
    parser.add_argument(
        '-dec', '--decompose', dest='decompose',
        help='perform residue decomposition analysis', action='store_true')
    parser.add_argument(
        '-ene', '--energy', dest='energy', help='gather total energy',
        action='store_true')
    parser.add_argument(
        '-res', '--residues', required=False, dest='resList',
        help='list of residue for which to decompose interaction energies (e.g. "1,2,3")',
        default=None)
    parser.add_argument(
        '-o', '--output', dest='outName', required=True)

    args = parser.parse_args()

    main(args)
