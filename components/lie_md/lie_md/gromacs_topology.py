# -*- coding: utf-8 -*-

"""
file: gromacs_setup.py

Function for prepairing input definitions for a GROMACS
Linear Interaction Energy MD calculation
"""

import os
import sys
import logging
import re


def correctItp(topfile,topOutFn, posre=True, outitp={}, removeMols=[], replaceMols=[], excludePosre=[], excludeHH=[], miscMols=[]):
    """
    Correct hydrogen and heavy atom masses in the .itp file
    makes position restraint file for the ligand
    outitp={'atomtypes': {'outfile':'attype.itp', 'overwrite':True}}
    """

    print "CORRECT ITP"

    if posre:
        posreNm="%s-posre.itp"%os.path.splitext(os.path.basename(topOutFn))[0]
    else:
        posreNm=None

    #read itp
    print "READ TOP"
    blocks,listBlocks,listMols=readCard(topfile)

    print "REMOVE MOLS"
    # remove mols;  eg. WAT to be substituted with SOL in amber to gromacs conversion
    blocks,listBlocks,listMols=topRmMols(blocks,listBlocks,removeMols)

    print "REPLACE MOLS"
    blocks,listBlocks=topReplaceMols(blocks,listBlocks,replaceMols)

    print "HH"
    #apply heavy hydrogens(HH)
    newBlocks=heavyH(listBlocks, blocks, listMols, excludeList=excludeHH)

    print "POSRES"
    #create positional restraints file
    if posre:
        posreNm=outPosre(blocks,listBlocks, listMols, excludePosre)
    else:
        posreNm={}

    print "ADD MOLS"
    #add additional moleculetypes (e.g. solvent and ions)
    miscBlocks,miscListBlocks,miscListMols=([],[],[])
    for mol in miscMols:
        b,lb,lm=readCard(mol)
        miscBlocks+=b
        miscListBlocks+=lb
        miscListMols+=lm 
    
    fixNewBlocks,fixListBlocks=itpAddMols(blocks,listBlocks, miscBlocks, miscListBlocks)

    # replace mols in system definition
     
    print "OUT ITP"
    #write corrected itp (with HH and no atomtype section
    topOut, extItps=itpOut(fixNewBlocks,fixListBlocks,topOutFn,posre=posreNm, excludeList=outitp)

    results={
             'top':topOut,
             'posre':[ posreNm[i] for i in posreNm],
             'externalItps':extItps
             }

    return results


def readCard(filetop):
    logging.debug('read topology')
    
    blockNames=[]
    listBlocks=[]

    title=False
    read=False

    with open(filetop,'r') as itp:
        block=[]
        for line in itp:
            atom=[]
            if line.startswith('#'):
                if block!=[]:
                    listBlocks.append(block)
                    block=[]
                listBlocks.append(line)
                blockNames.append(None)
            else:          
                line_sp=re.split('\s*',line[:-1])
                for item in line_sp:
                    if re.match(";",item):              
                        break

                    elif item == "[":
                        if block!=[]:
                            listBlocks.append(block)
                            block=[]
                        title=True
                        read=False
                    elif item=="]":
                        title=False
                        read=True
                    elif (title==True) and (item!=''):
                        blockNames.append(item)
                    elif (read==True) and (item!=''):
                        atom.append(item)
                if (atom!=[]):
                    block.append(atom)
    if block!=[]:
        listBlocks.append(block)

    # for molecule get:
    #    name
    #    index of the block with atoms
    #    index of block with bonds
    listMols=[]
    mol={}
    for nbl, blockNm in enumerate(blockNames):
        if blockNm == 'moleculetype':
            if len(mol)>0:
                listMols.append(mol)
            mol={}
            mol['name']=listBlocks[nbl][0][0]
        elif blockNm == 'atoms':
            mol['atoms']=nbl
        elif blockNm == 'bonds':
            mol['bonds']=nbl     

    if len(mol)>0:
        listMols.append(mol)


    return (listBlocks, blockNames, listMols)


def topRmMols(blocks,blockNames,mols2Del):
    print "TOP RM MOLS"
    popOut=False
    listOut=[]
    for nbl,blName in enumerate(blockNames):
        if blName=='moleculetype':
            print blocks[nbl][0][0]
            if blocks[nbl][0][0] in mols2Del:
                popOut=True
            else:
                popOut=False
        if blName=='system':
            popOut=False
        
        if popOut:
            listOut.append(nbl)
    
    listOut.sort(reverse=True)
    print "EXCLUDE", listOut
    for nbl in listOut:
        blocks.pop(nbl)
        blockNames.pop(nbl)
    
    print "CREATE LISTMOLS"
    listMols=[]
    mol={}
    for nbl, blockNm in enumerate(blockNames):
        if blockNm == 'moleculetype':
            if len(mol)>0:
                listMols.append(mol)
            mol={}
            mol['name']=blocks[nbl][0][0]
        elif blockNm == 'atoms':
            mol['atoms']=nbl
        elif blockNm == 'bonds':
            mol['bonds']=nbl     

    if len(mol)>0:
        listMols.append(mol)
    print "LISTMOLS  ", listMols 

    return (blocks,blockNames,listMols)


def topReplaceMols(blocks,blockNames,mols2Rep):
    # nol2Rep: [{'in':'WAT','out':'SOL'},..] 
    print 'TOPREPLACE'
    listin=[x['in'] for x in mols2Rep]
    for nbl,blName in enumerate(blockNames):
        if blName=='molecules':
            for mol in blocks[nbl]:
                print mol
                if mol[0] in listin:
                    mol[0]=mols2Rep[listin.index(mol[0])]['out']
                print mol
    
    return (blocks,blockNames)


def heavyH(blockNames, blocks,listMols, excludeList=['WAT']):
    '''Adjust the weights of hydrogens, and their heavy atom partner'''
    for mol in listMols:
        if mol['name'] not in excludeList:
            print mol
            for bond in blocks[mol['bonds']]:
                for hI in [0,1]:
                    if re.match("^h|^H", blocks[mol['atoms']][int(bond[hI])-1] [1]):
                        if hI==0:
                            hJ=1
                        elif hI==1:
                            hJ=0

                        ## Change heavy atom (heavy -3*H)               
                        blocks[mol['atoms']][int(bond[hJ])-1][7]=("%.5f" % ( float(blocks[mol['atoms']][int(bond[hJ])-1][7]) \
                                                                              - float(blocks[mol['atoms']][int(bond[hI])-1][7])*3  )  )
                        ## Change hydrogen (4*H)
                        blocks[mol['atoms']][int(bond[hI])-1][7]=("%.5f" % ( float(blocks[mol['atoms']][int(bond[hI])-1][7])*4) )    

    return(blocks)


def outPosre(blocks,listBlocks, listMols, excludeList):
    outposre={}
    for mol in listMols:
        if mol['name'] not in excludeList:
            oitp='%s-posre.itp'%mol['name']
            outposre[mol['name']]=oitp
            with open(oitp,"w") as outFile:
                outFile.write(\
'#ifndef 1POSCOS\n\
  #define 1POSCOS 10000\n\
#endif\n\
#ifndef 2POSCOS\n\
  #define 2POSCOS 5000\n\
#endif\n\
#ifndef 3POSCOS\n\
  #define 3POSCOS 2000\n\
#endif\n\
#ifndef 4POSCOS\n\
  #define 4POSCOS 1000\n\
#endif\n\
[ position_restraints ]\n')
                for atom in blocks[mol['atoms']]:
                    if not atom[4].startswith('H'):
                        if atom[3] == 'HEM':
                            outFile.write("%-4s    1  1POSCOS 1POSCOS 1POSCOS\n" % atom[0])
                        elif atom[4] in ['CA','N','O','C']:
                            outFile.write("%-4s    1  1POSCOS 1POSCOS 1POSCOS\n" % atom[0])
                        elif atom[4] in ['CB']:
                            outFile.write("%-4s    1  2POSCOS 2POSCOS 2POSCOS\n" % atom[0])
                        elif atom[4] in ['CG']:
                            outFile.write("%-4s    1  3POSCOS 3POSCOS 3POSCOS\n" % atom[0])
                        else:
                            outFile.write("%-4s    1  4POSCOS 4POSCOS 4POSCOS\n" % atom[0]) 
 
    return outposre


def itpAddMols(blocks, nameBlocks, miscBlocks, miscNameBlocks):
    
    ##FIX ATOMTYPES
    idxTypes=nameBlocks.index('atomtypes')
    idxNewTypes=[ i for i,x in enumerate(miscNameBlocks) if x=='atomtypes']
   
    for AttypeBlock in idxNewTypes:
        for newAtm in miscBlocks[AttypeBlock]:
            addAtm=True
            for atm in blocks[idxTypes]:
                if newAtm[0]==atm[0]:
                    addAtm=False
                    break
            if addAtm:
                blocks[idxTypes].append(newAtm)
            
    ## ADD MOLECULETYPE
    # new molecules are added before the system statement   
    idxSystem=nameBlocks.index('system')
    blNoAty=0
    for bl in range(len(miscNameBlocks)):
        if bl not in idxNewTypes:
            insIdx=idxSystem+blNoAty
            blocks.insert(insIdx,miscBlocks[bl])
            nameBlocks.insert(insIdx,miscNameBlocks[bl])
            blNoAty+=1
    
    return blocks, nameBlocks
    

def itpOut(blocks,nameBlocks,oitp,posre,excludeList={}):
    '''write new top. blocks defined in excludeList are removed and saved in the file 'outfile'. e.g atomtypes'''
    def outPosre(posreFN):
        outFile.write('#ifdef POSRES\n#include "%s"\n#endif\n\n'%posreFN)

    def outBlock(blockName,block,output):
        output.write("[ %s ]\n"%blockName)
        outFormat=defineFMTblock(block)
        for item in block:
            output.write(outFormat.format(d=item))

    extItps=[]
    with open(oitp,"w") as outFile:
        molWithPosre=False
        molName=None
        for nbl, blockName in enumerate(nameBlocks):
            if blockName is None:     # preprocessing instructions
                outFile.write(blocks[nbl])
    
            elif blockName in excludeList:        # specific itp
                #WRITE EXTERNAL ITP TO INCLUDE IF REQUIRED
                if excludeList[blockName]['overwrite']:
                    openMode='w'
                else:
                    openMode='a'
                with open(excludeList[blockName]['outfile'],openMode) as outItp:
                    outBlock(blockName,blocks[nbl],outItp)
                extItps.append(excludeList[blockName]['outfile'])
                outFile.write('#include "%s"\n\n'%excludeList[blockName]['outfile'])
                # outitp
            else:
                # WRITE INCLUDE POSRE IF REQUIRED
                if blockName=='moleculetype':
                    if molWithPosre:
                        outPosre(posre[molName])
                    molName=blocks[nbl][0][0]
                    if molName in posre:
                        molWithPosre=True
                    else:
                        molWithPosre=False
                if blockName=='system':
                    if molWithPosre:
                        outPosre(posre[molName])

                # PRINT OUT BLOCK
                outBlock(blockName,blocks[nbl],outFile)

            outFile.write("\n")

    return oitp,extItps

      
def defineFMTblock(block):
    listFmt=[]
    for atom in block:
        for i,item in enumerate(atom):
            try:
                listFmt[i].append(len(item))
            except IndexError:
                listFmt.append([len(item)])

    nchars=[max(x)+2 for x in listFmt]
    fmtOut=""
    for n,col in enumerate(nchars):
        fmtOut=fmtOut+"{d[%d]:>%ds}"%(n,col)
    fmtOut=fmtOut+"\n"

    return fmtOut


def correctAttype(itp,newtypes):
    oldtypes=[x[0] for x in itp['atomtypes']]   
    for attype in newtypes:
        if not attype[0] in oldtypes:
            itp['atomtypes'].append(attype) 

    return itp
