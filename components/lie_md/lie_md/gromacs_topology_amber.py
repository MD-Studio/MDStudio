# -*- coding: utf-8 -*-

"""
This file contains the functions for creation of topologies in amber format.
createTopology function should receive an input file
 (already processed  e.g. protonated)
and return a tuple containing itp and pdb of the ligand.
"""
import numpy as np
import os
from parsers import (itp_parser, parser_atoms_mol2, parse_file)
from twisted.logger import Logger

logger = Logger()

formats_dict = {
    "defaults":
    "{:>16s}{:>16s}{:>16s}{:>8s}{:>8s}\n",
    "atomtypes":
    "{:>3s}{:>9s}{:>17s}{:>9s}{:>4s}{:>16s}{:>14s}\n",
    "moleculetype": "{:>5s}{:>4s}\n",
    "atoms":
    "{:>6s}{:>5s}{:>6s}{:>6s}{:>6s}{:>5s}{:>13s}{:>13s}\n",
    "pairs": "{:>6s}{:>7s}{:>7s}\n",
    "bonds": "{:>6s}{:>7s}{:>4s}{:>14s}{:>14s}\n",
    "angles":
    "{:>6s}{:>7s}{:>7s}{:>6s}{:>14s}{:>14s}\n",
    "dihedrals":
    "{:>6s}{:>7s}{:>7s}{:>7s}{:>7s}{:>11s}{:>11s}{:>11s}{:>11s}{:>11s}{:>11s}\n",
    "dihedrals_2":
    "{:>6s}{:>7s}{:>7s}{:>7s}{:>7s}{:>9s}{:>10s}{:>4s}\n",
    "exclusions": "{:>5s}{:>5s}\n"}


def correctItp(itp_file, new_itp_file, posre=True):
    '''Correct hydrogen and heavy atom masses in the .itp file
       makes position restraint file for the ligand'''
    if posre:
        posreNm = "{}-posre.itp".format(
            os.path.splitext(new_itp_file)[0])
    else:
        posreNm = None

    # read itp
    itp_dict, ordered_keys = read_include_topology(itp_file)

    # apply heavy hydrogens(HH)
    itp_dict = adjust_heavyH(itp_dict)

    # write corrected itp (with HH and no atomtype section
    write_itp(itp_dict, ordered_keys, new_itp_file, posre=posreNm)

    # create positional restraints file
    if posre:
        write_posre(itp_dict, posreNm)
    # get charge ligand
    charge = sum(float(atom[6]) for atom in itp_dict['atoms'])

    return {'itp': new_itp_file, 'posre': posreNm,
            'attypes': itp_dict['atomtypes'],
            'charge': int(charge)}


def read_include_topology(itp_file):
    """
    Read an include topology file and returns a dictionary
    based on the sections.

    :param itp_file: path to the itp file
    :returns: dict
    """
    rs = parse_file(itp_parser, itp_file)

    # tranform the result into a dict
    vals = rs[0][1::2]
    unique_keys = create_unique_keys(rs[0][0::2])
    d = {k: np.array(v) for k, v in zip(unique_keys, vals)}

    return d, unique_keys


def create_unique_keys(xs):
    """
    List of unique block names
    """
    ys = []
    for key in xs:
        ys.append(check_name(key, ys))

    return ys


def check_name(key, ys):
    """Rename a key if already present in the list"""
    if key in ys:
        key = '{}_2'.format(key)
    return key


def adjust_heavyH(itp_dict):
    """
    Adjust the weights of hydrogens, and their heavy atom partner
    """
    # Indices of the hydrogens and their heavy companions
    hs, ps = compute_index_hs_and_partners(itp_dict)

    # Count the number of hydrogens attached to the heavy atoms
    heavy, coordination = np.unique(ps, return_counts=True)

    # Update the weights
    new_atoms = adjust_atom_weight(
        itp_dict['atoms'], hs, heavy, coordination)
    itp_dict['atoms'] = new_atoms

    return itp_dict


def adjust_atom_weight(atoms, hs, heavy, coordination):
    """
    Weight the masses of the `atoms` specificied  in `indices`
    using the `weights`.
    """
    mass_hydrogen = float(atoms[hs[0], 7])
    masses_hs = 4 * np.array(atoms[hs, 7], dtype=np.float)
    masses_heavy = np.array(atoms[heavy, 7], dtype=np.float)
    new_heavy_mass = masses_heavy - 3 * mass_hydrogen * coordination

    # Array to string
    fmt_hs = ['{:.4f}'.format(x) for x in masses_hs]
    fmt_heavy = ['{:.4f}'.format(x) for x in new_heavy_mass]

    # Update weights
    atoms[hs, 7] = fmt_hs
    atoms[heavy, 7] = fmt_heavy

    return atoms


def compute_index_hs_and_partners(itp_dict):
    """
    Extract the indices of the hydrogens and their heavy partners
    Assuming the the hydrogens are always listed after the heavy
    partner.
    """
    atoms = itp_dict['atoms']
    bonds = itp_dict['bonds']

    # Extract the bond indices
    bs = np.array(bonds[:, :2], dtype=np.int) - 1

    # Hydrogen indices
    symbols = atoms[bs[:, 1], 1]
    idxs = np.where([x.startswith(('h', 'H')) for x in symbols])
    hs = bs[idxs, 1]

    # Heavy partners
    ps = bs[idxs, 0]

    return hs.flatten(), ps.flatten()


def write_itp(itp_dict, keys, oitp, posre=None, excludeList=['atomtypes']):
    """
    write new itp. atomtype block is removed
    """
    with open(oitp, "w") as outFile:
        for block_name in keys:
            if block_name not in excludeList:
                outFile.write("[ {} ]\n".format(check_block_name(block_name)))
                for item in itp_dict[block_name]:
                    outFile.write(formats_dict[block_name].format(*item))
        outFile.write("\n")
        if posre is not None:
            outFile.write(
                '#ifdef POSRES\n#include "%s"\n#endif\n' % posre)


def check_block_name(block_name):
    """
    Check whether a block_name has been rename
    """
    if block_name.endswith('_2'):
        block_name = block_name[:-2]

    return block_name


def write_posre(itp_dict, output_itp):
    """
    Write position restraint itp file.
    """
    header = """
#ifndef 3POSCOS
  #define 2POSCOS 5000
#endif

#ifndef 5POSCOS
  #define 5POSCOS 0
#endif

[ position_restraints ]
"""
    with open(output_itp, "w") as f:
        f.write(header)
        for atom in itp_dict['atoms']:
            if atom[1].lower().startswith("h"):
                f.write(
                    "{}-4s    1  5POSCOS 5POSCOS 5POSCOS\n".format(atom[0]))
            else:
                f.write(
                    "{}-4s    1  2POSCOS 2POSCOS 2POSCOS\n".format(atom[0]))


def reorderhem(
        file_input, file_output='reordered.pdb',
        path_to_hem_template=None,
        listchange=None, diffres=0):
    """
    reorder the atom names for heme according to:
    J Comput Chem. 2012 Jan 15;33(2):119-33

    patch non standard water residue names and other pdb feature
    for amber topology creation
    """
    # Read HEME file specification
    new_order = read_hem_template(path_to_hem_template)

    with open(file_output, 'w') as f_out, open(file_input, 'r') as f_inp:
        pdb_lines = f_inp.readlines()
        f_out.write(create_new_pdb(pdb_lines, new_order))


def read_hem_template(path_to_hem_template):
    """
    Retrieve all the atoms in the @<TRIPOS>ATOM section.
    """
    rs = parse_file(parser_atoms_mol2, path_to_hem_template)
    return np.array(rs[0])


def create_new_pdb(pdb_lines, new_order):
    """
    Write the new order PDB file
    """
    pass
    # fmt = [(6, 't'), (5, 'i'), (5, 't'), (4, 't'), (2, 't'), (4, 'i'),

    #        (12, 'f'), (8, 'f'), (8, 'f'), (6, 'f'), (6, 'f')]
    # fmtout = "{:<6s}{:>5d}{:>5s}{:>4s}{:>2s}{:>4d}{:>12.3f}{:>8.3f}{:>8.3f}{:>6.2f}{:>6.2f}\n"
    # output = []
    # hem = []
    # oldline = ''
    # for line in pdb_lines:
    #     ishetatm=False
    #     if line.startswith("TER"):
    #         output.append(line)
    #     elif line.startswith("ATOM"):
    #         resname = line.split()[3]
    #         ishetatm = any(resname == t for t in ["HEM", "HOH", "WAT", "H2O"])
    #         if not ishetatm:
    #             process_atom_lines()

# def process_atom_lines(line):
        
#     else:
#         newln=[]
#         oldline=line
#         for col in fmt:
#             if col[1]=='t':
#                 newln.append(oldline[0:col[0]].strip())
#             elif col[1]=='i':
#                 newln.append(int(oldline[0:col[0]]))
#             elif col[1]=='f':
#                 newln.append(float(oldline[0:col[0]]))
#             oldline=oldline[col[0]:]
    
#         pos=next(( (i,change)
#             for i, change in enumerate(listchange)
#             if newln[5]+diffres in change ),
#             None)
#         if pos is not None:
#             if newln[3]==listchange[pos[0]][1]:
#                 newln[3]=listchange[pos[0]][2]
#             else:
#                 raise Exception, "Residue number and name do not correspond: Maybe the list of histidines and so on is not the right one (script is not perfect" 
#         output.write(fmtout.format(d=newln))
#         if newln[2]=='OXT':            # After automatic adjustment of histidines with reduce and saving file with openbabel, TER line is removed. OXT is the carbossiterminal atom. 
#             output.write('TER\n')

    #     elif line.startswith("HETATM"):
    #         ishetatm=True           

    #     if ishetatm:
    #         atm=line.split()
    #         newln=[]
    #         oldline=line
    #         for col in fmt:
    #             if col[1]=='t':
    #                 newln.append(oldline[0:col[0]].strip())
    #             elif col[1]=='i':
    #                 newln.append(int(oldline[0:col[0]]))
    #             elif col[1]=='f':
    #                 newln.append(float(oldline[0:col[0]]))
    #             oldline=oldline[col[0]:]

    #         if atm[3]=='HEM':
    #             hem.append(newln)
    #             #print newln
    #         elif atm[3]=='HOH' or atm[3]=='WAT' or atm[3]=='H2O':
    #             wat.append(newln)      

    #     oldline=line

    # if len(hem)>0:
    #     atmidx=sorted([x[1] for x in hem])[0]
    
    #     for atmid in range(len(neworder)):
    #         atmnm=neworder[atmid][1]
    #         pos=next(((i,atm.index(atmnm)) 
    #             for i, atm in enumerate(hem)
    #             if atmnm in atm),
    #             None)
    #         if pos is not None:
    #             hem[pos[0]][1]=atmidx
    #             output.write(fmtout.format(d=hem[pos[0]]))
    #             atmidx+=1
    #     output.write('TER\n')

    # if len(wat)>0:
    #     print "Add water molecules"
    #     for lnatm in wat:
    #         lnatm[1]=atmidx
    #         lnatm[0]='ATOM'
    #         lnatm[3]='WAT'
    #         output.write(fmtout.format(d=lnatm))
    #         atmidx+=1
    #         output.write('TER\n')
            
    # output.write('END\n')


# AMBERHOME = os.environ['AMBERHOME']

# tleap = join(AMBERHOME, 'bin/tleap')
# ambpdb = join(AMBERHOME, 'bin/ambpdb')
# solventMols = join(__rootpath__, 'scripts/solventAmber.itp')


# def convertAmber2PQR(prmtop,inpcrd,outprefix):
#     with open(inpcrd, 'r') as coordfile:
#         coords=coordfile.read()
    
#     locEnv=os.environ.copy()
#     locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
#     locEnv['AMBERHOME']=AMBERHOME

#     cmd =  [ambpdb, '-p', prmtop, '-pqr']
#     apdbProc=sp.Popen(cmd, env=locEnv,stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.PIPE)
#     out=apdbProc.communicate(input=coords)[0]
#     pqr=out
#     ## PATCH FOR OPENBABEL 11/2015
#     pqrtemp=''
#     for line in pqr.splitlines():
#         pqrtemp='%s%s\n'%(pqrtemp,line[0:75])

#     pqr=pqrtemp

#     refconfMol=pybel.readstring('pqr',pqr)

#     return refconfMol
    

# def createProtSystem(pdbin,outprefix,nhem,ncyp,cypCoord=True):
#     locEnv=os.environ.copy()
#     locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
#     locEnv['AMBERHOME']=AMBERHOME
#     bondCyp=''
#     if nhem is not None:
#         if cypCoord:
#             bondCyp="bond prot.%d.28 prot.%d.8"%(nhem,ncyp)
#         else:
#             bondCyp="bond prot.%d.28 prot.%d.13"%(nhem,ncyp)

#     prepare_sys('mini',pdbin,outprefix,nhem,ncyp,misc=bondCyp)
#     cmd =  [tleap, '-f', 'xleap.inp']
#     ac=sp.call(cmd, env=locEnv)

#     if not ( os.path.exists("%s.prmtop"%outprefix) and os.path.exists("%s.inpcrd"%outprefix)):
#         raise Exception('Error in amber topology creation. Check the input.')
    
#     return ("%s.prmtop"%outprefix,"%s.inpcrd"%outprefix)


# def prepareGMX(pbMol,prmtop,inpcrd,outNamePref,protTop=None,moreMols=solventMols):
#     confTop,confGro=convertAmber2GMX(prmtop,inpcrd)
    
#     # in case water is present in the original PDB convert "amber" WAT in gromacs 'SOL'
#     solAmber={'name':'WAT','atoms':['O','H1','H2']}
#     solGromacs={'name':'SOL','atoms':['OW','HW1','HW2']}
#     replaceMols={'in':solAmber['name'], 'out':solGromacs['name']}
#     print "CORRECTGRO"
#     confGro=topology.correctGro(confGro,solAmber,solGromacs)
    
#     if protTop is None:
#         topOutFn='%s.top'%outNamePref
#         outitp={'atomtypes': {'outfile':'attype.itp', 'overwrite':True}}
#         listTop=topology.correctItp(confTop,topOutFn, posre=True, outitp=outitp, removeMols=['WAT'],replaceMols=[replaceMols], \
#                                     excludePosre=['WAT'], excludeHH=['WAT'],miscMols=moreMols)
#         charge=getChargelog('leap.log')

#         currDir=os.getcwd()
#         confTop=os.path.join(currDir,listTop['top'])
#         attype=os.path.join(currDir,listTop['externalItps'][0])
#         posre=os.path.join(currDir,listTop['posre'][0])

#     else:
#         success=gmxTest(protTop,confGro)
#         attype=None
#         posre=None
#         charge=None
#         if not success:
#             raise Exception("Checking top-gro match FAILED")

#     return (confTop, confGro, attype, posre,charge)  
        

# def convertAmber2GMX(prmtop,inpcrd):
#     print "CONVERT TO GMX: %s, %s"%(prmtop, inpcrd)
#     locEnv=os.environ.copy()
#     locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
#     locEnv['AMBERHOME']=AMBERHOME    
#     cmd =  [ACPYPE, '-p', prmtop, '-x',inpcrd]
#     pacpype=sp.Popen(cmd, env=locEnv)
#     pacpype.wait()
#     pref=os.path.splitext(os.path.split(prmtop)[1])[0]
#     outtop=os.path.join(os.getcwd(),'%s_GMX.top'%(pref))
#     pref=os.path.splitext(os.path.split(inpcrd)[1])[0]
#     outgro=os.path.join(os.getcwd(),'%s_GMX.gro'%pref)

#     if (not os.path.exists(outtop)) and (not os.path.exists(outgro)):
#         raise Exception('Error in elaboration of the PDB file. Check the input.')

#     return (outtop,outgro)


# def prepare_sys(preset, pdbin,output,nhem,ncyp,misc=''):
#     '''This function sets up docking with PLANTS so that CMD can be executed by the script.
#      Requires the protein for docking as separate input. The other arguments should be named and are passed to Conf().'''

#     settings={'preset': preset,
#             'key'   :{
#             'pdb'  : pdbin,
#             'hemid': nhem,
#             'cypid': ncyp,
#             'out'  : output,
#             'misc' : misc
#             }
#             }

#     conf = xleapinp(DATADIR)
  
#     conf.setCustom(**settings)
    
#     with open('xleap.inp','w') as inputf:
#         inputf.write(conf.mode('custom'))


# class xleapinp:

#     def __init__(self, dirparams):
#         self.text=textwrap.dedent('''
#         source leaprc.ff14SB
#         source leaprc.gaff
#         loadamberparams {0[frcmod]}
#         loadoff {0[hemeoff]}
#         loadoff {0[cypoff]}
#         loadoff {0[hihoff]}
#         prot=loadpdb {0[pdb]}
#         {0[misc]}
#         charge prot
#         saveamberparm prot {0[out]}.prmtop {0[out]}.inpcrd
#         savepdb prot {0[out]}.pdb
#         quit''').strip('\n')

#         self.mini=dict(
#         frcmod=os.path.join(dirparams,'IC6.frcmod'),
#         hemeoff=os.path.join(dirparams,'HEME_IC6.off'),
#         cypoff=os.path.join(dirparams,'CYP_IC6.off'),
#         hihoff=os.path.join(dirparams,'hih.off'),
#         pdb='input.pdb',
#         out='output.pdb',
#         misc=''           
#         )
        
#         self.sim=dict(
#         frcmod=os.path.join(dirparams,'CPDI.frcmod'),
#         hemeoff=os.path.join(dirparams,'HEME_CPDI.off'),
#         cypoff=os.path.join(dirparams,'CYP_CPDI.off'),
#         hihoff=os.path.join(dirparams,'hih.off'),
#         pdb='input.pdb',
#         out='output.pdb',
#         misc=''           
#         )
        
#         if "self.customset" not in locals():
#             self.customset=self.sim.copy()


#         self.presets = {'mini': self.mini,
#                         'sim' : self.sim,
#                         'custom': self.customset
#                         }
    
#     def setCustom(self,**kwargs):
#     # User can set the individual values in the custom preset to whatever is desired
#     # use key= and value= to change one value.
#     # Its also possible to change the entire list to one predefined preset with preset=
#         if 'preset' in kwargs:
#             self.customset=self.presets.get(kwargs['preset'])      
#         else:
#             raise Exception, 'Use a preset value (mini, sim)!'
        
#         if 'key' in kwargs:
#             for key in kwargs['key']:
#                 self.customset[key]=kwargs['key'][key]
#             self.presets['custom']=self.customset

#         #elif 'key' in kwargs and 'val' in kwargs and len(kwargs) == 2:
#         #    self.customset[kwargs['key']]=kwargs['val']
#         #else:
#         #    raise Exception, 'Use preset=, or key= and val= as arguments!'   
        
#     def mode(self,preset):
#         # Returns formatted xleap configuration file with values set to preset requested.
#         if preset in self.presets:          
#             return self.text.format(self.presets[preset])
#         else:
#             raise Exception, 'Unknown preset!'


# def getChargelog(logleap):
#     with open(logleap) as f:
#         for line in f:
#             if line.startswith("Total unperturbed charge:"):
#                 charge=float(line.split(":")[1])
#                 break 
#     return charge


# def correctAttype(itp,newtypes):
    
#     oldtypes=[x[0] for x in itp['atomtypes']]
    
#     for attype in newtypes:
#         if not attype[0] in oldtypes:
#             itp['atomtypes'].append(attype) 

#     return itp


# def refineTau(filein,listChanges, nhem, ncyp, outPref, cypCoord=True):
#     # cypCoord True if the coordinating group is a cysteine, otherwise histidine, called HIH. 
#     # Parameters are fine only if HEM is not directly interacting
#     print 'refineTau'
    
#     print listChanges
#     print nhem,ncyp
#     outOrdered=reorderhem(filein,fileout='%s_ordered.pdb'%outPref,listchange=listChanges)

#     print 'amber.py: refineTau to createProtSystem'
#     outprmtop,outinpcrd=createProtSystem(outOrdered,outPref,nhem,ncyp,cypCoord=cypCoord)
    
#     print outprmtop
#     # print as pqr, since openbabel is able to recognize atom properties (not the case with mol2) and charges
#     confMol=convertAmber2PQR(outprmtop,outinpcrd,outPref)
#     return (confMol,outprmtop,outinpcrd)
