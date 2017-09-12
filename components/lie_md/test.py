import os

from lie_md import __rootpath__
from lie_md.gromacs_topology_amber import *

protein_file = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/lieproject/1504520599/task-13-1504520640-7696/protein.pdb'
ligand_file = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/lieproject/1504520599/task-13-1504520640-7696/ligand.pdb'
topology_file = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/lieproject/1504520599/task-7-1504520600-8931/input.acpype'
GMXRC = 'path/to/gmx'

workdir = os.path.join(os.getcwd(), 'mdrun')

# Create workdir and save file
if not os.path.isdir(workdir):
    os.mkdir(workdir)
os.chdir(workdir)

# Store protein file if available
if protein_file:
    protdsc = os.path.join(workdir,'protein.pdb')
    try:
        if os.path.isfile(protein_file):
            shutil.copy(protein_file, protdsc)
    except:
        with open(protdsc, 'w') as inp:
            inp.write(protein_file)

# Store ligand file if available
if ligand_file:
    ligdsc = os.path.join(workdir,'ligand.pdb')
    try:
        if os.path.isfile(ligand_file):
            shutil.copy(ligand_file, ligdsc)
    except:     
        with open(ligdsc, 'w') as inp:
            inp.write(ligand_file)

# Save ligand topology files
if topology_file:
    topdsc = os.path.join(workdir,'ligtop.itp')
    try:
        if os.path.isfile(os.path.join(topology_file, 'input_GMX.itp')):
            shutil.copy(os.path.join(topology_file, 'input_GMX.itp'), topdsc)
    except:        
        with open(topdsc, 'w') as inp:
            inp.write(topology_file)

# Copy script files to the working directory
for script in ('getEnergies.py', 'gmx45md.sh'):
    src = os.path.join(__rootpath__, 'scripts/{0}'.format(script))
    dst = os.path.join(workdir, script)
    shutil.copy(src, dst)

#Fix topology ligand
itpOut = 'ligand.itp'
results = correctItp(topdsc, itpOut, posre=True)

# Prepaire simulation
gmx_cmd = {
    '-ff': 'amber99SB',
    '-charge': results['charge'], 
    '-lie': None,
    '-d': 1.8,
    '-t': '100,200,300',
    '-prfc': '10000,5000,50,0',
    '-ttau': 0.1,
    '-conc': 0,
    '-solvent': 'tip3p',
    '-ptau': 0.5,
    '-time': 1.0,
    '-vsite': None,
    '-gmxrc': GMXRC
}

if protein_file:
    gmx_cmd['-f'] = os.path.basename(protdsc)

if ligand_file:
    gmx_cmd['-l'] = '{0},{1}'.format(os.path.basename(ligdsc), os.path.basename(results['itp']))

gmxRun = './gmx45md.sh '
for arg,val in gmx_cmd.items():
    if val == None:
        gmxRun += '{0} '.format(arg)
    else:
        gmxRun += '{0} {1} '.format(arg,val)
    
# Prepaire post analysis (energy extraction)
eneRun = 'python getEnergies.py -gmxrc {0} -ene -o ligand.ene'.format(GMXRC)

# write executable
with open('run_md.sh','w') as outFile:
    outFile.write("{0}\n".format(gmxRun))
    outFile.write("{0}\n".format(eneRun))