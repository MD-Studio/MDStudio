#
# @cond ___LICENSE___
#
# Copyright (c) 2017 K.M. Visscher and individual contributors.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# @endcond
#

import yaml

from lie_md.common.exception import LieMdException
from lie_md.run_parameters.run_input_file import RunInputFile

def WriteHeader( run_input_file, gromacs_target, ofstream ):

    print( ";" )
    print( "; MDP File generated for GROMACS %s by MDStudio from run template version %s" % (gromacs_target, run_input_file.version) )
    print( ";" )

def WriteMdpString( key, value, ofstream ):

    print ( "%-25s = %s" % ( key, value) )

def WriteMdpInt( key, value, ofstream ):

    print ( "%-25s = %i" % ( key, value) )

def WriteMdpFloat( key, value, ofstream ):

    print ( "%-25s = %f" % ( key, value) )

def HandleRunProperties1( run_input_file, gromacs_target, ofstream ):

    if not "run_properties" in run_input_file:
        raise LieMdException(  "GenerateMdp", "Block run_properties is required in the input")
    
    integrator_mapping = dict()
    integrator_mapping["leap-frog"]           = "md"
    integrator_mapping["velocity-verlet"]     = "md-vv"
    integrator_mapping["stochastic-dynamics"] = "sd"
    integrator_mapping["steepest-descent"]    = "steep"
    integrator_mapping["conjugate-gradient"]  = "cg"

    gromacs_integrator = integrator_mapping[ run_input_file.run_properties.integrator.value ]
    gromacs_start_time = run_input_file.run_properties.start_time.value
    gromacs_delta_time = run_input_file.run_properties.delta_time.value
    gromacs_steps      = run_input_file.run_properties.steps.value
    gromacs_init_step  = 0
    gromacs_seed       = run_input_file.run_properties.seed.value

    print( "\n; run_properties" )
    WriteMdpString( "integrator", gromacs_integrator, ofstream )
    WriteMdpFloat( "tinit", gromacs_start_time, ofstream )
    WriteMdpFloat( "dt", gromacs_delta_time, ofstream )
    WriteMdpInt( "nsteps", gromacs_steps, ofstream )
    WriteMdpInt( "init-step", gromacs_init_step, ofstream )
    WriteMdpInt( "ld-seed", gromacs_seed, ofstream )
    WriteMdpInt( "gen-seed", gromacs_seed, ofstream )

def HandleCenterOfMass1( run_input_file, gromacs_target, ofstream ):

    if not "center_of_mass" in run_input_file:
        raise LieMdException(  "GenerateMdp", "Block center_of_mass is required in the input")
    
    comm_mapping = dict()
    comm_mapping["linear"]  = "Linear"
    comm_mapping["angular"] = "Angular"
    comm_mapping["none"]    = "None"

    gromacs_comm_mode = comm_mapping[ run_input_file.center_of_mass.mode.value ]
    gromacs_comm_freq = run_input_file.center_of_mass.frequency.value
    gromacs_comm_grps = "System"
    
    print( "\n; center_of_mass" )
    WriteMdpString( "comm_mode", gromacs_comm_mode, ofstream )
    WriteMdpInt( "nstcomm", gromacs_comm_freq, ofstream)
    WriteMdpString( "comm_grps", gromacs_comm_grps, ofstream  )

def HandleEnergyMin1( run_input_file, gromacs_target, ofstream ):
    
    # Optional!
    if "minimization" in run_input_file:
        
        gromacs_tolerance  = run_input_file.minimization.tolerance.value
        gromacs_step_size  = run_input_file.minimization.step_size.value
        gromacs_steps      = run_input_file.minimization.steps.value
        gromacs_lbfgs_corr = 10

        print( "\n; minimization" )
        WriteMdpFloat( "emtol", gromacs_tolerance, ofstream )
        WriteMdpFloat( "emstep", gromacs_step_size, ofstream )
        WriteMdpInt(   "nstcgsteep", gromacs_steps, ofstream )
        WriteMdpInt(   "nbfgscorr", gromacs_lbfgs_corr, ofstream )

def GenerateMdp( run_input_file, gromacs_target, ofstream ):    

    run_input_file.Validate()

    version_mapping = dict()
    version_mapping[ ("1.0.0", "2016.3" ) ] = [ 
        WriteHeader, HandleRunProperties1, HandleCenterOfMass1, HandleEnergyMin1
     ]

    target = ( run_input_file.version, gromacs_target )

    if not target in version_mapping:
        raise LieMdException(  "GenerateMdp", "Target %s not present in version map" % ( str(target) ) )
    
    sequence = version_mapping[target]

    for seqitem in sequence:
        seqitem(run_input_file, gromacs_target, ofstream)
        
