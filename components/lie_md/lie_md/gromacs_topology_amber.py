# -*- coding: utf-8 -*-

"""
This file contains the functions for creation of topologies in amber format.
createTopology function should receive an input file (already processed  e.g. protonated)
and return a tuple containing itp and pdb of the ligand.
"""

import sys
import os
import pybel
import shutil
import logging
import re
import textwrap

import subprocess as sp
import gromacs_topology

from . import __rootpath__

AMBERHOME = '/opt/personal/amber16'

tleap=os.path.join(AMBERHOME, 'bin/tleap')
ambpdb=os.path.join(AMBERHOME, 'bin/ambpdb')
solventMols=os.path.join(__rootpath__, 'scripts/solventAmber.itp')

def correctItp(itpfile,itpOutFn, posre=True):
    '''Correct hydrogen and heavy atom masses in the .itp file
       makes position restraint file for the ligand'''
    if posre:
        posreNm="%s-posre.itp"%os.path.splitext(os.path.basename(itpOutFn))[0]
    else:
        posreNm=None
    
    #read itp
    itp,listItp=readCard(itpfile)
    #apply heavy hydrogens(HH)
    itp=heavyH(itp)
    #write corrected itp (with HH and no atomtype section 
    itpOut(itp,listItp,itpOutFn,posre=posreNm)   
    #create positional restraints file
    if posre:
        outPosre(itp,posreNm)
    #get charge ligand
    charge=0
    for atom in itp['atoms']:
        charge+=float(atom[6])

    results={'itp':itpOutFn,
             'posre':posreNm,
             'attypes':itp['atomtypes'],
             'charge':int(charge)}        

    return results


def readCard(fileitp):
    logging.debug('read topology')
    card={}
    cardOrder=[]
    block=[]
    title=False
    read=False
    with open(fileitp,'r') as itp:
        for line in itp:
            atom=[]
            line_sp=re.split(' *',line[:-1])
            for item in line_sp:
                if re.match(";",item):              
                    break
                elif item == "[":
                    if block!=[]:
                        card[nameBlock]=block
                        cardOrder.append(nameBlock)
                        nameBlock=''
                        block=[]
                    title=True
                    read=False
                elif item=="]":
                    title=False
                    read=True
                elif (title==True) and (item!=''):
                    nameBlock=item
                elif (read==True) and (item!=''):
                    atom.append(item)
            if (atom!=[]):
                block.append(atom)
    if block!=[]:
        card[nameBlock]=block
        cardOrder.append(nameBlock)

    return card, cardOrder


def heavyH(card):
    '''Adjust the weights of hydrogens, and their heavy atom partner'''
    atomBlock=card['atoms']
    for bond in card['bonds']:
        for i in [0,1]:
            if re.match("^h|^H", card['atoms'][int(bond[i])-1][1]):
                if i==0:
                    j=1
                elif i==1:
                    j=0
                ## Change heavy atom (heavy -3*H)               
                atomBlock[int(bond[j])-1][7]=("%.4f" % ( float(card['atoms'][int(bond[j])-1][7]) - float(card['atoms'][int(bond[i])-1][7])*3  )  ) 
                ## Change hydrogen (4*H)
                atomBlock[int(bond[i])-1][7]=("%.4f" % ( float(card['atoms'][int(bond[i])-1][7])*4) )

    card['atoms']=atomBlock
    
    return(card)


def itpFormat(block):
    formatTemplate = {
        "defaults" : "{d[0]:>16s}{d[1]:>16s}{d[2]:>16s}{d[2]:>8s}{d[2]:>8s}\n",
        "atomtypes" : "{d[0]:>3s}{d[1]:>9s}{d[2]:>17s}{d[3]:>9s}{d[4]:>4s}{d[5]:>16s}{d[6]:>14s}\n",
        "moleculetype" : "{d[0]:>5s}{d[1]:>4s}\n",
        "atoms" : "{d[0]:>6s}{d[1]:>5s}{d[2]:>6s}{d[3]:>6s}{d[4]:>6s}{d[5]:>5s}{d[6]:>13s}{d[7]:>13s}\n",
        "pairs" : "{d[0]:>6s}{d[1]:>7s}{d[2]:>7s}\n",
        "bonds" : "{d[0]:>6s}{d[1]:>7s}{d[2]:>4s}{d[3]:>14s}{d[4]:>14s}\n",
        "angles" : "{d[0]:>6s}{d[1]:>7s}{d[2]:>7s}{d[3]:>6s}{d[4]:>14s}{d[5]:>14s}\n",
        "dihedrals" : "{d[0]:>6s}{d[1]:>7s}{d[2]:>7s}{d[3]:>7s}{d[4]:>7s}{d[5]:>11s}{d[6]:>11s}{d[7]:>11s}{d[8]:>11s}{d[9]:>11s}{d[10]:>11s}\n",
        "dihedrals2" : "{d[0]:>6s}{d[1]:>7s}{d[2]:>7s}{d[3]:>7s}{d[4]:>7s}{d[5]:>9s}{d[6]:>10s}{d[7]:>4s}\n",
        "exclusions" : "{d[0]:>5s}{d[1]:>5s}\n"
    }
    
    return(formatTemplate[block])


def itpOut(card,listCard,oitp,posre=None,excludeList=['atomtypes']):
    '''write new itp. atomtyep block is removed'''
    with open(oitp,"w") as outFile:
        for blockName in listCard:
            if not blockName in excludeList:
                outFile.write("[ %s ]\n"%blockName)
                for item in card[blockName]:
                    try:
                        outFile.write(itpFormat(blockName).format(d=item))
                    except:
                        outFile.write(itpFormat("%s2"%blockName).format(d=item))
        outFile.write("\n")
        if posre is not None:
            outFile.write('#ifdef POSRES\n#include "%s"\n#endif\n'%posre)

    return

      
def outPosre(itp,oitp):
    with open(oitp,"w") as outFile:
        outFile.write("#ifndef 3POSCOS\n  #define 2POSCOS 5000\n#endif\n\n#ifndef 5POSCOS\n  #define 5POSCOS 0\n#endif\n\n[ position_restraints ]\n")  
        for atom in itp['atoms']:
            if atom[1].lower().startswith("h"):
                outFile.write("%-4s    1  5POSCOS 5POSCOS 5POSCOS\n" % atom[0])
            else:
                outFile.write("%-4s    1  2POSCOS 2POSCOS 2POSCOS\n" % atom[0])

    return


def correctAttype(itp,newtypes):
    
    oldtypes=[x[0] for x in itp['atomtypes']]
    
    for attype in newtypes:
        if not attype[0] in oldtypes:
            itp['atomtypes'].append(attype) 

    return itp



#### FUNCTIONS FOR PROTEIN PREPARATION


def refineTau(filein,listChanges, nhem, ncyp, outPref, cypCoord=True):
    # cypCoord True if the coordinating group is a cysteine, otherwise histidine, called HIH. 
    # Parameters are fine only if HEM is not directly interacting
    print 'refineTau'
    
    print listChanges
    print nhem,ncyp
    outOrdered=reorderhem(filein,fileout='%s_ordered.pdb'%outPref,listchange=listChanges)

    print 'amber.py: refineTau to createProtSystem'
    outprmtop,outinpcrd=createProtSystem(outOrdered,outPref,nhem,ncyp,cypCoord=cypCoord)
    
    print outprmtop
    # print as pqr, since openbabel is able to recognize atom properties (not the case with mol2) and charges
    confMol=convertAmber2PQR(outprmtop,outinpcrd,outPref)
    return (confMol,outprmtop,outinpcrd)


def reorderhem(filein,fileout='reordered.pdb',listchange=None, waterfn=None, diffres=0):
    # reorder the atom names for heme according to J Comput Chem. 2012 Jan 15;33(2):119-33
    # patch non standard water residue names and other pdb feature for amber topology creation
    fmt=[(6,'t'),(5,'i'),(5,'t'),(4,'t'),(2,'t'),(4,'i'),(12,'f'),(8,'f'),(8,'f'),(6,'f'),(6,'f')]
    fmtout="{d[0]:<6s}{d[1]:>5d}{d[2]:>5s}{d[3]:>4s}{d[4]:>2s}{d[5]:>4d}{d[6]:>12.3f}{d[7]:>8.3f}{d[8]:>8.3f}{d[9]:>6.2f}{d[10]:>6.2f}\n"
    fmtoutmol2="{d[0]:>7s}{d[1]:>5s}{d[2]:>14.4f}{d[3]:>10.4f}{d[4]:>10.4f}{d[5]:>10s}{d[6]:>5s}{d[7]:>5s}{d[8]:>10s}\n"
    
    wat=[]
    if waterfn is not None:
        #print "Reading file with water molecules"
        input=open(waterfn,'r')
        templ=input.readlines()
        for line in templ:
            if line.startswith("HETATM"):
                atm=line.split()
                newln=[]
                oldline=line
                for col in fmt:
                    if col[1]=='t':
                        newln.append(oldline[0:col[0]].strip())
                    elif col[1]=='i':
                        newln.append(int(oldline[0:col[0]]))
                    elif col[1]=='f':
                        newln.append(float(oldline[0:col[0]]))
                    oldline=oldline[col[0]:]            
                #print newln
                if atm[3]=='HOH':
                    wat.append(newln)
                    print "wat", newln

    #print 'reorder HEME'
    neworder=[]
    readln=False
    head=True
    with open(hemeTemplate) as temphem:
        for line in temphem:
            linesp=line.split()
            if len(linesp)>0:
                if linesp[0]=="@<TRIPOS>BOND":
                    readln=False
                    head=False
                if readln == True:            
                    neworder.append(linesp)
                if linesp[0]=="@<TRIPOS>ATOM":
                    readln=True
    
    input=open(filein,'r')
    templ=input.readlines()
    input.close()
    output=open(fileout,'w')
    hem=[]
    oldline=''
    #print 'check HETATMs'
    for line in templ:
        ishetatm=False
        if line.startswith("TER"):
            output.write(line)
        elif line.startswith("ATOM"):
            resname=line.split()[3]
            if resname=="HEM" or resname=="HOH" or resname=="WAT" or resname=="H2O":
                ishetatm=True
            else:
                newln=[]
                oldline=line
                for col in fmt:
                    if col[1]=='t':
                        newln.append(oldline[0:col[0]].strip())
                    elif col[1]=='i':
                        newln.append(int(oldline[0:col[0]]))
                    elif col[1]=='f':
                        newln.append(float(oldline[0:col[0]]))
                    oldline=oldline[col[0]:]
    
                pos=next(( (i,change)
                    for i, change in enumerate(listchange)
                    if newln[5]+diffres in change ),
                    None)
                if pos is not None:
                    if newln[3]==listchange[pos[0]][1]:
                        newln[3]=listchange[pos[0]][2]
                    else:
                        raise Exception, "Residue number and name do not correspond: Maybe the list of histidines and so on is not the right one (script is not perfect" 
                output.write(fmtout.format(d=newln))
                if newln[2]=='OXT':            # After automatic adjustment of histidines with reduce and saving file with openbabel, TER line is removed. OXT is the carbossiterminal atom. 
                    output.write('TER\n')

        elif line.startswith("HETATM"):
            ishetatm=True           

        if ishetatm:
            atm=line.split()
            newln=[]
            oldline=line
            for col in fmt:
                if col[1]=='t':
                    newln.append(oldline[0:col[0]].strip())
                elif col[1]=='i':
                    newln.append(int(oldline[0:col[0]]))
                elif col[1]=='f':
                    newln.append(float(oldline[0:col[0]]))
                oldline=oldline[col[0]:]

            if atm[3]=='HEM':
                hem.append(newln)
                #print newln
            elif atm[3]=='HOH' or atm[3]=='WAT' or atm[3]=='H2O':
                wat.append(newln)      

        oldline=line

    if len(hem)>0:
        atmidx=sorted([x[1] for x in hem])[0]
    
        for atmid in range(len(neworder)):
            atmnm=neworder[atmid][1]
            pos=next(((i,atm.index(atmnm)) 
                for i, atm in enumerate(hem)
                if atmnm in atm),
                None)
            if pos is not None:
                hem[pos[0]][1]=atmidx
                output.write(fmtout.format(d=hem[pos[0]]))
                atmidx+=1
        output.write('TER\n')

    if len(wat)>0:
        print "Add water molecules"
        for lnatm in wat:
            lnatm[1]=atmidx
            lnatm[0]='ATOM'
            lnatm[3]='WAT'
            output.write(fmtout.format(d=lnatm))
            atmidx+=1
            output.write('TER\n')
            
    output.write('END\n')
    output.close()
    
    return os.path.join(os.getcwd(),fileout)


def convertAmber2PQR(prmtop,inpcrd,outprefix):
    with open(inpcrd, 'r') as coordfile:
        coords=coordfile.read()
    
    locEnv=os.environ.copy()
    locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
    locEnv['AMBERHOME']=AMBERHOME

    cmd =  [ambpdb, '-p', prmtop, '-pqr']
    apdbProc=sp.Popen(cmd, env=locEnv,stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.PIPE)
    out=apdbProc.communicate(input=coords)[0]
    pqr=out
    ## PATCH FOR OPENBABEL 11/2015
    pqrtemp=''
    for line in pqr.splitlines():
        pqrtemp='%s%s\n'%(pqrtemp,line[0:75])

    pqr=pqrtemp

    refconfMol=pybel.readstring('pqr',pqr)

    return refconfMol
    

def createProtSystem(pdbin,outprefix,nhem,ncyp,cypCoord=True):
    locEnv=os.environ.copy()
    locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
    locEnv['AMBERHOME']=AMBERHOME
    bondCyp=''
    if nhem is not None:
        if cypCoord:
            bondCyp="bond prot.%d.28 prot.%d.8"%(nhem,ncyp)
        else:
            bondCyp="bond prot.%d.28 prot.%d.13"%(nhem,ncyp)

    prepare_sys('mini',pdbin,outprefix,nhem,ncyp,misc=bondCyp)
    cmd =  [tleap, '-f', 'xleap.inp']
    ac=sp.call(cmd, env=locEnv)

    if not ( os.path.exists("%s.prmtop"%outprefix) and os.path.exists("%s.inpcrd"%outprefix)):
        raise Exception('Error in amber topology creation. Check the input.')
    
    return ("%s.prmtop"%outprefix,"%s.inpcrd"%outprefix)


def prepareGMX(pbMol,prmtop,inpcrd,outNamePref,protTop=None,moreMols=solventMols):
    confTop,confGro=convertAmber2GMX(prmtop,inpcrd)
    
    # in case water is present in the original PDB convert "amber" WAT in gromacs 'SOL'
    solAmber={'name':'WAT','atoms':['O','H1','H2']}
    solGromacs={'name':'SOL','atoms':['OW','HW1','HW2']}
    replaceMols={'in':solAmber['name'], 'out':solGromacs['name']}
    print "CORRECTGRO"
    confGro=topology.correctGro(confGro,solAmber,solGromacs)
    
    if protTop is None:
        topOutFn='%s.top'%outNamePref
        outitp={'atomtypes': {'outfile':'attype.itp', 'overwrite':True}}
        listTop=topology.correctItp(confTop,topOutFn, posre=True, outitp=outitp, removeMols=['WAT'],replaceMols=[replaceMols], \
                                    excludePosre=['WAT'], excludeHH=['WAT'],miscMols=moreMols)
        charge=getChargelog('leap.log')

        currDir=os.getcwd()
        confTop=os.path.join(currDir,listTop['top'])
        attype=os.path.join(currDir,listTop['externalItps'][0])
        posre=os.path.join(currDir,listTop['posre'][0])

    else:
        success=gmxTest(protTop,confGro)
        attype=None
        posre=None
        charge=None
        if not success:
            raise Exception("Checking top-gro match FAILED")

    return (confTop, confGro, attype, posre,charge)  
        

def convertAmber2GMX(prmtop,inpcrd):
    print "CONVERT TO GMX: %s, %s"%(prmtop, inpcrd)
    locEnv=os.environ.copy()
    locEnv['PATH']=locEnv['PATH']+':'+AMBERHOME
    locEnv['AMBERHOME']=AMBERHOME    
    cmd =  [ACPYPE, '-p', prmtop, '-x',inpcrd]
    pacpype=sp.Popen(cmd, env=locEnv)
    pacpype.wait()
    pref=os.path.splitext(os.path.split(prmtop)[1])[0]
    outtop=os.path.join(os.getcwd(),'%s_GMX.top'%(pref))
    pref=os.path.splitext(os.path.split(inpcrd)[1])[0]
    outgro=os.path.join(os.getcwd(),'%s_GMX.gro'%pref)

    if (not os.path.exists(outtop)) and (not os.path.exists(outgro)):
        raise Exception('Error in elaboration of the PDB file. Check the input.')

    return (outtop,outgro)


def gmxTest(top,gro):
    def gmx_min(output):
        text=textwrap.dedent('''
            cpp                      = /usr/bin/cpp
            define                   =
            integrator               = cg
            nstcgsteep               = 50
            emtol                    = 1
            nsteps                   = 1000
            emstep                   = 0.001
            nstcomm                  = 1
            ns_type                  = grid
            nstlist                  = 1
            rlist                    = .9
            coulombtype              = Cut-off
            rcoulomb                 = 1.4
            vdwtype                  = Cut-off
            rvdw                     = 1.4
            Tcoupl                   = no
            Pcoupl                   = no
            constraints              = h-bonds
            constraint-algorithm     = LINCS
            lincs-order              = 8
            lincs-iter               = 2
            gen_vel                  = no
            nstxout                  = 10
            pbc                      = no
        ''').strip('\n')
        
        inputf=open(output,'w')
        inputf.write(text)
        inputf.close()
    
    # Perfom minimization
    locEnv=os.environ.copy()
    gmx_min('test.mdp')
    cmd = [grompp, '-f', 'test.mdp', '-p', top, '-c', gro, '-o', 'test.tpr']
    grmp=sp.Popen(cmd, env=locEnv)
    grmp.wait()
    
    if os.path.exists('test.tpr'):
        success=True
        os.remove('test.tpr')
    else:
        success=False
    
    return success


def prepare_sys(preset, pdbin,output,nhem,ncyp,misc=''):
    '''This function sets up docking with PLANTS so that CMD can be executed by the script.
     Requires the protein for docking as separate input. The other arguments should be named and are passed to Conf().'''

    settings={'preset': preset,
            'key'   :{
            'pdb'  : pdbin,
            'hemid': nhem,
            'cypid': ncyp,
            'out'  : output,
            'misc' : misc
            }
            }

    conf = xleapinp(DATADIR)
  
    conf.setCustom(**settings)
    
    with open('xleap.inp','w') as inputf:
        inputf.write(conf.mode('custom'))


class xleapinp:

    def __init__(self, dirparams):
        self.text=textwrap.dedent('''
        source leaprc.ff14SB
        source leaprc.gaff
        loadamberparams {0[frcmod]}
        loadoff {0[hemeoff]}
        loadoff {0[cypoff]}
        loadoff {0[hihoff]}
        prot=loadpdb {0[pdb]}
        {0[misc]}
        charge prot
        saveamberparm prot {0[out]}.prmtop {0[out]}.inpcrd
        savepdb prot {0[out]}.pdb
        quit''').strip('\n')

        self.mini=dict(
        frcmod=os.path.join(dirparams,'IC6.frcmod'),
        hemeoff=os.path.join(dirparams,'HEME_IC6.off'),
        cypoff=os.path.join(dirparams,'CYP_IC6.off'),
        hihoff=os.path.join(dirparams,'hih.off'),
        pdb='input.pdb',
        out='output.pdb',
        misc=''           
        )
        
        self.sim=dict(
        frcmod=os.path.join(dirparams,'CPDI.frcmod'),
        hemeoff=os.path.join(dirparams,'HEME_CPDI.off'),
        cypoff=os.path.join(dirparams,'CYP_CPDI.off'),
        hihoff=os.path.join(dirparams,'hih.off'),
        pdb='input.pdb',
        out='output.pdb',
        misc=''           
        )
        
        if "self.customset" not in locals():
            self.customset=self.sim.copy()


        self.presets = {'mini': self.mini,
                        'sim' : self.sim,
                        'custom': self.customset
                        }
    
    def setCustom(self,**kwargs):
    # User can set the individual values in the custom preset to whatever is desired
    # use key= and value= to change one value.
    # Its also possible to change the entire list to one predefined preset with preset=
        if 'preset' in kwargs:
            self.customset=self.presets.get(kwargs['preset'])      
        else:
            raise Exception, 'Use a preset value (mini, sim)!'
        
        if 'key' in kwargs:
            for key in kwargs['key']:
                self.customset[key]=kwargs['key'][key]
            self.presets['custom']=self.customset

        #elif 'key' in kwargs and 'val' in kwargs and len(kwargs) == 2:
        #    self.customset[kwargs['key']]=kwargs['val']
        #else:
        #    raise Exception, 'Use preset=, or key= and val= as arguments!'   
        
    def mode(self,preset):
        # Returns formatted xleap configuration file with values set to preset requested.
        if preset in self.presets:          
            return self.text.format(self.presets[preset])
        else:
            raise Exception, 'Unknown preset!'


def getChargelog(logleap):
    with open(logleap) as f:
        for line in f:
            if line.startswith("Total unperturbed charge:"):
                charge=float(line.split(":")[1])
                break 
    return charge
