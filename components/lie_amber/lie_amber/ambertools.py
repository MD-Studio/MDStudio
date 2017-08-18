# -*- coding: utf-8 -*-

import os
import logging
import copy

from twisted.logger import Logger

from .cli_runner import CLIRunner
from .settings import SETTINGS

logging = Logger()


def amber_acpype(mol, workdir=None, **kwargs):
    """
    Run the ACPYPE program (AnteChamber PYthon Parser interfacE)
    
    acpype reference:
    - Sousa da Silva AW, Vranken WF. ACPYPE - AnteChamber PYthon 
      Parser interfacE. (2012), BMC Res Notes. 2012 Jul 23;5:367.
      doi: 10.1186/1756-0500-5-367.
    """
    
    # ACPYPE executable is part of the package
    lie_amber_path = os.path.dirname(os.path.realpath(__file__))
    acepype_exe_path = os.path.join(lie_amber_path, 'acpype.py')
    
    # Check the input file
    if not os.path.exists(mol):
        logging.error('Input file does not exist {0}'.format(mol))
    
    # Construct CLI arguments
    options = copy.deepcopy(SETTINGS['amber_acpype'])
    options.update(dict([(k.lower().strip('-'),v) for k,v in kwargs.items()]))
    
    # Process sqm/mopac keywords
    if 'keyword' in options:
        options['keyword'] = '"{0}"'.format(options['keyword'].strip('"'))
    
    # Process boolean flags
    flags = ['--{0}'.format(option) for option,flag in options.items() if flag == True]
    
    # Process keyword argument flags
    flags = ['--{0} {1}'.format(option, flag) for option,flag in options.items() if 
        type(flag) not in (bool,type(None))]
    
    logging.info("Running ACPYPE with command line arguments: {0}".format(','.join(flags)))
    not_supported = ['--{0}'.format(n) for n in kwargs if not n.lower() in SETTINGS['amber_acpype']]
    if not_supported:
        logging.warn("Following command line arguments not supported by ACPYPE: {0}".format(','.join(not_supported)))
    
    workdir_name = os.path.splitext(mol)[0]
    cmd = [acepype_exe_path, '-i', mol] + flags
    
    # Run the CLI command
    clirunner = CLIRunner(directory=workdir)
    runner = clirunner.run(cmd)
    
    output_path = os.path.join(workdir, '{0}.acpype'.format(workdir_name))
    if runner.succeeded and os.path.isdir(output_path):
        return output_path
    else:
        logging.error('Acpype failed')

def amber_reduce(mol, output=None, return_output_path=False, exe='reduce', **kwargs):
    """
    Run AmberTools "reduce" program for adding hydrogens to molecular
    structures.
    
    The `amber_reduce` function supports all of the reduce command line
    options available in reduce version 3.24 shipped with AmberTools 16.
    Options may be turned on or off by default using the module wide
    settings or be set specifically by providing the command line option
    as keyword argument to the function.
    
    Options that may be added in future versions of reduce will be made
    availabe by adding them to the module wide settings.
    
    Please consult the reduce documentation in the pdf manual:
    - http://ambermd.org/doc12/Amber16.pdf
    
    reduce reference:
    - Word, et. al. (1999) Asparagine and Glutamine: Using Hydrogen Atom
      Contacts in the Choice of Side-chain Amide Orientation,
      J. Mol. Biol. 285, 1733-1747.
    
    :param mol:     file path to input structure in PDB file format
    :type mol:      :py:str
    :param output:  file path to output structure in PDB file format
                    Defaults to the input path with '_h.pdb' added as
                    prefix.
    :type output:   :py:str
    :param return_output_path: return the path to the output PDB file 
                    instead of the contents of the file itself.
    :type return_output_path: :py:bool
    :param exe:     name of the 'reduce' executable as available in the
                    amber bin directory defined by the 'amberhome' 
                    variable in the module settings (defaults to the
                    AMBER_HOME environmental variable).
    :type exe:      :py:str
    """
    
    # Define executable
    reduce_exe_path = os.path.join(SETTINGS['amberhome'], 'bin', exe)
    
    # Check the input file
    if not os.path.exists(mol):
        logging.error('Input file does not exist {0}'.format(mol))
    
    # Define output file
    if not output:
        output = '{0}_h{1}'.format(*os.path.splitext(mol))
    
    # Construct CLI arguments
    options = copy.deepcopy(SETTINGS['amber_reduce'])
    options.update(dict([(k.lower().strip('-'),v) for k,v in kwargs.items()]))
    
    # Process boolean flags
    flags = ['-{0}'.format(option) for option,flag in options.items() if flag == True]
    
    # Process keyword argument flags
    flags.extend(['-{0}{1}'.format(option, flag) for option,flag in options.items() if 
        type(flag) not in (bool,type(None))])
    
    logging.info("Running Amber 'reduce' with command line arguments: {0}".format(','.join(flags)))
    not_supported = ['-{0}'.format(n) for n in kwargs if not n.lower() in SETTINGS['amber_reduce']]
    if not_supported:
        logging.warn("Following command line arguments not supported by Amber 'reduce': {0}".format(','.join(not_supported)))
    
    cmd = [reduce_exe_path] + flags
    cmd.extend([mol, '>', output])
    
    # Run the CLI command    
    clirunner = CLIRunner()
    clirunner.run(cmd)
    
    # Return output file
    if os.path.exists(output):
        if return_output_path:
            return output
        else:
            with open(output, 'r') as out:
                return out.read()
    else:
        logging.error('Reduce failed, not output file {0}'.format(output))
    