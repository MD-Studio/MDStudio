from __future__ import print_function
'''
Tool to gather ensemble energies and per-residue decomposed energies from gromacs md files (edr and trr for decomposition)
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
import os
import re
import subprocess as sp
import sys

from glob import glob
from tempfile import NamedTemporaryFile
from twisted.logger import Logger

logging = Logger()


def getGMXEnv(gmxrc):
    command = ['bash', '-c', 'source %s && env' % gmxrc]
    proc = sp.Popen(command, stdout=sp.PIPE)
    newEnv = {}
    for line in proc.stdout:
        (key, _, value) = line.partition("=")
        newEnv[key] = value.rstrip()
    proc.communicate()

    return newEnv


def parseResidues(strinput):
    indexmol = []
    tempindexmol = strinput.split(',')
    for item in tempindexmol:
        if len(item.split('-')) == 1:
            indexmol.append(int(item))
        elif len(item.split('-')) == 2:
            indexmol += range(
                int(item.split('-')[0]),
                int(item.split('-')[1]) + 1)
    else:
        raise Exception("Invalid list,%i" % len(item.split('-')))
    indexmol = sorted(set(indexmol))

    return indexmol


def availProg(prog, myEnv):
    for path in myEnv["PATH"].split(os. pathsep):
        cmd = os.path.join(path, prog)
        if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
            return True

    return False


def findFile(wdir, ext='edr', pref=''):
    findString = os.path.join(wdir, "%s.%s" % (pref, ext))
    listfound = glob(findString)
    if len(listfound) == 0:
        msg = 'No file found: %s' % findString
        return False, msg

    if len(listfound) > 1:
        # Additional option for selection could be implented here
        print(listfound)
        msg = 'I don\'t know what to do! Multiple files found: %s.'%findString
        return False, msg

    if len(listfound) == 1:
        return True, listfound[0]


def getEne(fileEne, gmxEnv, listRes=['Ligand']):
    #Execute gmxdump
    cmd=['gmxdump','-e', fileEne]

    # use two space delimiter to split column from ene file
    # (To include terms like "LJ (SR)" )
    splitFormat = r'\s{2,}' 
    
    potentialLab = ['Potential']
    kineticLab = ['Kinetic En.']
    tLab = ['Temperature']
    eleLab = ['Coulomb-14','Coulomb (SR)','Coulomb (LR)', 'Coul. recip.']
    vdwLab = ['LJ-14','LJ (SR)','LJ (LR)']

    eleDecLab = ['Coul-14','Coul-SR']
    vdwDecLab=['LJ-14','LJ-SR']
    tDecLab = ['T-']

    eneCard = []
    frame={}

    outpipe=NamedTemporaryFile(mode='w+b')   #open('cacca','w+b')#
    out=open(outpipe.name,'r+b')
    proc=sp.Popen(cmd,stdout=outpipe,stderr=sp.PIPE, env=gmxEnv, bufsize=-1)
    where = 0 #out.tell()

    while True:
        out.seek(where)
        line = out.readline()

        if not line:
            #out.seek(where)
            outLine=''
        else:
            where=out.tell()
            outLine=str(line) # already has newline

        errLine=proc.stderr.readline()
        if proc.poll() != None:
            out.seek(0,2)
            end=out.tell()
            out.seek(where)
            if end == where:
                if outLine == '' and errLine == '':
                    break

        if outLine != '':
            outLine_sp=re.split(splitFormat, outLine.rstrip().lstrip()) #strip to remove empty space at the beginning and \n at the end
            ### Here analyze energy file on the fly
            # new frame

            if outLine_sp[0]=='time:':
                if bool(frame):
                    eneCard.append(frame)
                frame={}
                frame['time']=float(outLine_sp[1])
                frame['step']=int(outLine_sp[3])
                frame['vdw']=0
                frame['ele']=0
                
            # temperature
            
            if outLine_sp[0] in tLab:
                frame[outLine_sp[0]]=float(outLine_sp[1])
            # potential
            if outLine_sp[0] in potentialLab:
                frame[outLine_sp[0]]=float(outLine_sp[1])        
            #kinetic
            if outLine_sp[0] in kineticLab:
                frame[outLine_sp[0]]=float(outLine_sp[1])        
            # Electrostatic
            if outLine_sp[0] in eleLab:      
                frame['ele']+=float(outLine_sp[1])
            # van der Waals
            if outLine_sp[0] in vdwLab:      
                frame['vdw']+=float(outLine_sp[1])
    
            ### Decomposition
            if 'time' in frame:
                try:
                    eneterm,label=outLine_sp[0].split(':')           
                    group1,group2=label.split('-')
                    if group1 in listRes:
                        if group1 != group2:
                            #check if already defined
                            if not '%s-ele'%label in frame:
                                frame['%s-ele'%label]=0
                                frame['%s-vdw'%label]=0
                            # Ele terms
                            if eneterm in eleDecLab:
                                frame['%s-ele'%label]+=float(outLine_sp[1])
                            # vdw terms
                            if eneterm in vdwDecLab:
                                frame['%s-vdw'%label]+=float(outLine_sp[1])
                except ValueError:
                    continue
    
            proc.stderr.flush()
        #Now repeat until end of gmxdump
    out.close()
    outpipe.close()
    
    if bool(frame):
        eneCard.append(frame)

    if proc.returncode != 0:
        raise Exception, "something went wrong during energy gathering"  

    return eneCard


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
            logging.debug("OUT: %s"%outLine)
            logging.debug("ERR: %s"%errLine)
            sys.stdout.flush()
            sys.stderr.flush()
    except Exception, e:
        logging.error(e)
        return False
    return True


def decomp(mdpDict, resList, ndx, gro, top, trr, gmxEnv, ligGroup='Ligand',outPref='decompose',suff4ndx='sol'):
    listkeys=['include', 'define', 'cutoff-scheme', 'ns-type', 'pbc', 'periodic-molecules', 'rlist', 'rlistlong', 'nstcalclr',\
               'coulombtype','coulomb-modifier','rcoulomb-switch', 'rcoulomb', 'epsilon-r', 'epsilon-rf', \
               'vdw-type','vdw-modifier','rvdw-switch','rvdw','DispCorr', \
               'table-extension', 'energygrp-table', 'fourierspacing', 'fourier-nx', 'fourier-ny', 'fourier-nz', \
               'pme-order','ewald-rtol','ewald-geometry','epsilon-surface','optimize-fft','implicit-solvent','QMMM',\
               'constraints', 'constraint-algorithm', 'continuation', 'Shake-SOR', 'shake-tol', \
               'lincsorder', 'lincs-iter', 'lincs-warnangle', 'morse', \
               'nwall', 'wall-type', 'wall-r-linpot', 'wall-atomtype', 'wall-density', 'wall-ewald-zfac',\
               'pull', 'rotation', 'disre', \
               'orire','free-energy','simulated-tempering']

    newKeys={'nstxout': '0',
             'nstvout': '0',
             'nstfout': '0',
             'nstlog': '0',
             'nstcalcenergy': '1',
             'nstenergy': '1',
             'nstxtcout': '0',
             'xtc-precision': '0',
             'xtc-grps': '',
             'nstlist' : '1',            
             }
    newKeys['energygrps']=ligGroup 
    for res in resList:
        newKeys['energygrps']+=' %d'%res
    
    outMdp="%s.mdp"%outPref
    with open(outMdp,'w') as outFile:
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

    
    ### run rerun
    cmd=['grompp', '-f', outMdp, '-c', gro, '-p', top, '-n', outNdx, '-o', outTpr]
    success=executeProg(cmd,gmxEnv)
    if not success:
        msg='Something went wrong in the creation of the tpr file  for decomposition analysis'
        return (False,msg)
        
    cmd=['mdrun', '-s', outTpr, '-rerun', trr, '-deffnm', outPref]
    success=executeProg(cmd,gmxEnv)
    if not success:
        msg='Something went wrong in the rerun decomposition analysis'
        return (False,msg)
    
    return (True,outPref)


parser = argparse.ArgumentParser(
    description='Dock sdf file into protein conformation')

parser.add_argument(
    '-gmxrc', required=False, dest='gmxrc',
    help='GMXRC file for environment loading')
parser.add_argument(
    '-d', '--dir', required=False,
    dest='dataDir', help='directory with MD files to process', default=None)
parser.add_argument(
    '-dec', '--decompose', dest='decompose',
    help='perform residue decomposition analysis', action='store_true')
parser.add_argument(
    '-ene', '--energy', dest='energy',
    help='gather total energy', action='store_true')
parser.add_argument(
    '-res', '--residues', required=False, dest='resList',
    help='list of residue for which to decompose interaction energies (e.g. "1,2,3")', default=None)
parser.add_argument(
    '-o', '--output',dest='outName', required=True)

args = parser.parse_args()


logging.basicConfig(level='INFO')
### Data dir definition
if args.dataDir is not None:
    dataDir=args.dataDir
else:
    dataDir=os.getcwd()

### output file
outName=args.outName

### Create gromacs environment
if args.gmxrc is not None:
    gmxEnv=getGMXEnv(args.gmxrc)
else:
    gmxEnv=os.environ

### Full energy gathering
if args.energy and args.decompose:
    logging.error('Make a decision: decomposition (-dec) or ensemble energy gathering (-ene)!')
    sys.exit(-1)

if args.energy:
    cmd='gmxdump'
    if availProg(cmd,gmxEnv):
        success,results=findFile(dataDir,ext='edr',pref='*?MD*')
        if success:
            listFrames=getEne(results,gmxEnv)
        else:
            logging.error(results)
            sys.exit(1)
        
        labs2print=['time', 'Potential', 'Kinetic En.', 'Temperature', 'ele', 'vdw', 'Ligand-Ligenv-ele', 'Ligand-Ligenv-vdw']
        writeOut(listFrames,outName,labs2print)       
    else:
        logging.error('TERMINATED. Program %s not found.'%cmd)
        sys.exit(1)
        

### Per-residue energy decomposition
if args.decompose:
    if args.resList is None:
        logging.error('TERMINATED. List of residues not provided.')
        sys.exit(1)

    if not (availProg('grompp',gmxEnv) and availProg('mdrun',gmxEnv) and availProg('gmxdump',gmxEnv)):
        logging.error('TERMINATED. Programs required for decomposition not found.')
        sys.exit(1)

    resList=parseResidues(args.resList)
    mdpName='md-prod-out.mdp'
    mdpIn=os.path.join(dataDir,mdpName)
    #parse MD mdp
    mdpDict=parseMdp(mdpIn)
    #create decomposition mdp, ndx and run rerun
    success,gro=findFile(dataDir,ext='gro',pref='*?sol')
    success,ndx=findFile(dataDir,ext='ndx',pref='*?sol')
    success,trr=findFile(dataDir,ext='trr',pref='*?MD*')
    success,top=findFile(dataDir,ext='top',pref='*?sol')
    success,results=decomp(mdpDict,resList,ndx,gro,top,trr, gmxEnv)
    if not success:
        logging.error(results)
        sys.exit(1)    
    # Analysis of energy decomposition file after rerun
    success,results=findFile(dataDir,ext='edr',pref=results)
    if success:
        logging.debug("Extracting decomposed energies from %s file"%results) 
        listFrames=getEne(results,gmxEnv)
    else:
        logging.error(results)
        sys.exit(1)
    
    labs2print=['time','Potential','ele','vdw']+['Ligand-%d-vdw'%x for x in resList]+['Ligand-rest-vdw']+['Ligand-%d-ele'%x for x in resList]+['Ligand-rest-ele']

    writeOut(listFrames,outName,labs2print)

logging.info('SUCCESSFUL COMPLETION OF THE PROGRAM')
