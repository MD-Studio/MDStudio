# -*- coding: utf-8 -*-

"""
This file contains the functions to deal with atb in and output, or to cheat with topologies. Outdated!!!!
"""

import urllib2
import urllib
import cookielib
from time import sleep
from molhandle import *
from bs4 import BeautifulSoup
import os
import time
import shutil
import logging
import re

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as sp
else:
    import subprocess as sp

from .. import settings
AMBERHOME = settings.get('AMBERHOME')
ACPYPE = settings.get('ACPYPE')
ATB_URL = 'http://compbio.biosci.uq.edu.au/atb/'
LOGIN_URL = 'http://compbio.biosci.uq.edu.au/atb/login.py'
SUBMISSION_URL = 'http://compbio.biosci.uq.edu.au/atb/index.py'

file_list = [
  u'GROMOS96 All-Atom MTB', 
  u'GROMOS96 United-Atom MTB', 
  u'GROMOS96 United-Atom Topology',
  u'GROMOS11 All-Atom MTB',
  u'GROMOS11 United-Atom MTB',
  u'GROMACS G53A6FF All-Atom (ITP file)',
  u'GROMACS G53A6FF United-Atom (ITP file)',
  u'CIF G53A6 All-Atom',
  u'Extended CIF G53A6 All-Atom',
  u'CIF G53A6 United-Atom',
  u'Extended CIF G53A6 United-Atom',
  u'CNS G53A6 All-Atom (topology file)',
  u'CNS G53A6 All-Atom (parameter file)',
  u'CNS G53A6 United-Atom (topology file)',
  u'CNS G53A6 United-Atom (parameter file)',
  u'All-Atom PDB (optimised geometry)',
  u'All-Atom PDB (original geometry)',
  u'United-Atom PDB (optimised geometry)',
  u'United-Atom PDB (original geometry)',
  u'CIF All-Atom PDB',
  u'CIF United-Atom PDB',
  u'United-Atom G96 (optimised geometry)'
]
    
def ac_topo(ft,fn,wdir,addH=False):
  currdir=os.getcwd()
  logging.debug(ACPYPE)
  logging.debug(AMBERHOME)
  molecule = file_2_mol(ft,fn,addH) #translate file to molecule
  charge=molecule.charge
  acinp = mols_2_single([molecule],output='%s/atbinput'%wdir,format='mol2' ) 
  amberbin=os.path.join(AMBERHOME,'bin')
  os.environ['PATH']=os.environ['PATH']+':%s'%amberbin
  os.environ['AMBERHOME']=AMBERHOME
  os.chdir(wdir)
  cmd =  [ACPYPE, '-i', 'atbinput.mol2', '-n', str(charge)]
  out=''
  err=''
  ac=sp.call(cmd,stdout=sp.PIPE)
  logging.info('AC topology created with success')
  logging.info('copy the file in %s'%os.path.join(wdir,'atbinput.acpype','atbinput_GMX.itp'))
  shutil.copy(os.path.join(wdir,'atbinput.acpype','atbinput_GMX.itp'), wdir+'/atb1.txt')  
  shutil.copy(wdir+'/atbinput.acpype/atbinput_NEW.pdb',wdir+'/atb2.txt')
  atb_outputfiles=['atb1.txt','atb2.txt']
  os.chdir(currdir)

  return tuple(atb_outputfiles)
  

def ATB_login(credentials):
  '''Login to the ATB and provide a way to open the urls that uses our cookie'''
  #Make a jar to store the cookies
  cj = cookielib.CookieJar()
  
  #How to open the urls
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))  
  
  #Logging in through POST request
  req = urllib2.Request(LOGIN_URL, urllib.urlencode(credentials))
  #Retrieving the page
  raw_html_login = opener.open(req).read()
  # test if the login was successful
  login_success = 'sessionid' in [c.name for c in cj]
  
  return opener if login_success else None
  

def ATB_submit(ft,fn,wdir, opener,addH=False):
  '''format,filename,workdir, opener'''
  
  #convert whatever the input was to a pdb file
  molecule = file_2_mol(ft,fn,addH) #translate file to molecule  
  charge = molecule.charge
  atbinp = mols_2_single([molecule],output='%s/atbinput'%wdir,format='pdb' )
  
  #Read the text in the pdbfile generated by babel
  pdb = open('%s/atbinput.pdb'%wdir, 'r').read()
  logging.info("real submission") 
  #Form data for the submission
  submis_data = { 
  '.submit' : 'Submit',
  'tab' : 'submit_tab',
  'public' : 'public',
  'input' : 'test123',
  'moltype' : 'heteromolecule',
  'netcharge' : ("%s.0"%charge),
  'ff' : '53A6',
  'qm0choice' : 'AM1',
  'pdbfield' : pdb
  }
  
  #Submitting calculation through POST request
  logging.debug("get url")
  sub =  urllib2.Request(SUBMISSION_URL, urllib.urlencode(submis_data))
  #Retrieving the page  
  raw_html_submit = opener.open(sub).read()  
#  logging.debug("%s"%raw_html_submit)
  #Extract the download url from the page
  subsoup = BeautifulSoup(raw_html_submit.replace('<br \>','<br />'))
  DOWNLOAD_URL = None
  for div in  subsoup.find_all('div'):
    try:
      if div['class'][2] == u'#submit_tab':
        URL=div.a['href']
        logging.debug(URL)
        molid=re.split('=',URL)[1]
        DOWNLOAD_URL='molecule.py?molid=%s&outputType=top&atbVersion=v2Top&ffVersion=Gromos#files'%molid
    except  (KeyError, IndexError):    
      pass
  return DOWNLOAD_URL
  
def ATB_download(DOWNLOAD_URL,wdir,opener,downloads=[u'GROMACS G53A6FF United-Atom (ITP file)', u'All-Atom PDB (optimised geometry)']):
#def ATB_download(DOWNLOAD_URL,wdir,opener,downloads=[u'file=rtp_uniatom', u'file=pdb_allatom_optimised']):
  '''Url of download page, workdir, page opener, files to download'''
  logging.info("sending ATB request")
  dl = urllib2.Request(ATB_URL + DOWNLOAD_URL)
  #Wait for the ATB to finish processing
  logging.debug("%s      %s"%(ATB_URL,DOWNLOAD_URL))
  done = not True
  
  while not done:
    done = True
    #open the download page
    raw_html_download = opener.open(dl).read()    
    logging.debug(raw_html_download)
    dlsoup = BeautifulSoup(raw_html_download)
  
    #check all the h2 headers
    for h2 in dlsoup.find_all('h2'):      
      if h2.string == u'Processing Information:':        
      #Only ?session= urls have processing information. If you get a ?molid= link, you're (supposedly) already done.
        for table in dlsoup.find_all('table'):
        #find the table containing the processing state
          try:
            if table.find_all('td')[0].string == u'Current Processing State' and table.find_all('td')[1].string  != u'Completed':            
            #if it is not completed, it's not done
              done = not True  
          except IndexError:
            pass
  #to avoid overloading the network, powernap!
    if not done:
      sleep(300)
#  atb_outputfiles = list()
#  if not done:
#    atb_outputfiles.append('Topology building: partial')
#  else: 
  #Once we're done, it's time to compile a dictionary of links to files from the atb  
  logging.info("ATB request completed!")
  download_urls = dict()
  #for all links
  for table in re.split('table class="download_links_table">',raw_html_download):
    bstab=BeautifulSoup(table)
    logging.debug(bstab)
    #if the text of said link indicates an interesting file
    for a in bstab.find_all('a'):
      logging.debug(a.string)
      if a.string in file_list:
        #add that file to the dictionary, pointing to its link
        logging.debug("%s FOUND"%a.string)
        download_urls[a.string] = a['href']  
  
  #Download the files from ATB
  atb_outputfiles = list()
  for num,download in enumerate(downloads,start=1):   
    logging.info('%s&%s' %( ATB_URL,download_urls[download])) 
    dl_file = urllib2.Request('%s%s' %( ATB_URL,download_urls[download]))
    data = opener.open(dl_file).read()
    with open('%s/atb%d.txt'%(wdir,num), "wb") as code:
      code.write(data)  
    atb_outputfiles.append('atb%d.txt'%num)
    
  return tuple(atb_outputfiles)