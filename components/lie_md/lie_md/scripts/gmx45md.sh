##!/bin/bash
#shopt -s expand_aliases

PROGRAM=${0##*/}
VERSION=1.3 # 2012-07-28.2030
GMXVERSION=4.5.x
HISTORY="\
"

AUTHORS="Tsjerk A. Wassenaar, PhD"
YEAR="2012"
AFFILIATION="
VU University Amsterdam
De Boelelaan 1083
1081HV Amsterdam
The Netherlands"


DESCRIPTION=$(cat << __DESCRIPTION__

$PROGRAM $VERSION is a versatile wrapper for setting up and running
molecular dynamics simulations of proteins and/or nucleic acids in solvent.
The script contains a complete and flexible workflow, consisting of the 
following steps:

    1.   Generate topology from input structure 
         A. Process structure against force field (TOPOLOGY)
         B. Add ligands                           (LIGANDS)
    2.   Set up periodic boundary conditions      (BOX)
    3.   Energy minimize system in vacuum         (EMVACUUM)
    4.   Solvation and adding ions                (SOLVATION)
    5.   Energy minimization                      (EMSOL)
    6.   Position restrained NVT equilibration    (NVT-PR)
    7.   Unrestrained NpT equilibration           (NPT)
    8.   Equilibration under run conditions       (PREPRODUCTION)
    9.   Production simulation                    (PRODUCTION)

The program allows running only part of the workflow by specifying the
start and end step (-step/-stop), using an argument uniquely matching 
one of the tags given between parentheses.

This program requires a working installation of Gromacs $GMXVERSION. To link 
the program to the correct version of Gromacs, it should be placed in the 
Gromacs binaries directory or the Gromacs GMXRC file should be passed as 
argument to the option -gmxrc

The workflow contained within this program corresponds to a standard protocol
that should suffice for routine molecular dynamics simulations of proteins 
and/or nucleic acids in aqueous solution. It follows the steps that are 
commonly taken in MD tutorials (e.g. http://md.chem.rug.nl/~mdcourse/molmod2012/).

This program is designed to enable high-throughput processing of molecular
dynamics simulations in which specific settings are varied systematically. These
settings include protein/nucleic acid, ligand, temperature, and pressure, as well
as many others.


## -- IMPORTANT -- ##

Molecular dynamics simulations are complex, with many contributing factors. 
The workflow in this program has been tested extensively and used many times.
Nonetheless, it should not be considered failsafe. No MD protocol ever is. 
Despite careful set up, simulations may crash, and the possibility that a crash
is encountered is larger when many simulations are run. If the run crashes,
the intermediate results will be kept and can be investigated to identify the
source of the problem. 

If the run finishes to completion, this does not automatically imply that the
results are good. The results from the simulations should always be subjected
to integrity and quality assurance checks to assert that they are correct within
the objectives of the study.


__DESCRIPTION__
)


: << __NOTES__

This has grown to be a rather complicated bash script. Still, it is intended to 
work through the MD process as a person would, issuing shell commands and reading
and editing files, for which bash feels more natural. It is advised to (get to)
know about bash loops and variable substitution, as these are used plenty. 
In addition, since there are many occassions where files need to be read and 
edited, there are a lot of calls to sed, with quite a few less ordinary commands.
Unfortunately, some of these are specific to GNU sed, which causes this program
to fail on Mac.

To keep the code manageable, it is structured in sections and every section is
ordered, preferrably by numbered chunks. In addition, there is extensive 
documentation. Every statement should be clear, either by itself or by a 
preceding explanation. In case advanced bash/sed/... features are used, they 
ought to be explained. That will keep the program manageable and make it a nice
place for learning tricks :)

Oh, and please note that usual copyright laws apply...

TAW - 20120718

__NOTES__



#--------------------------------------------------------------------
#---GLOBAL PARAMETERS--
#--------------------------------------------------------------------

# Sed the right version of sed for multi-platform use.
SED=$( which gsed )
[ ! -n "$SED" ] && SED=$( which sed )

# Set the script directory
# This is the place where binaries are sought if -gmxrc is not given
SCRIPTDIR=$(cd ${0%${0##*/}}; pwd)
GMXBIN=$SCRIPTDIR


#--------------------------------------------------------------------
#---PARSING COMMAND LINE ARGUMENTS--
#--------------------------------------------------------------------


# Run control and files
DIR="."           
fnIN=             
NAME=
TOP=
FETCH=false
ARCHIVE=
FORCE=false
EXEC=
NP=1
MDP=
MDARGS=
GMXRC=
JUNK=()


# Stepping stuff
STEPS=(TOPOLOGY LIGANDS BOX EMVACUUM SOLVATION EMSOLVENT NVT-PR NPT PREPRODUCTION PRODUCTION END)
STEP=TOPOLOGY 
STOP=END


# Force field
ForceFieldFamilies=(gromos  charmm  amber   opls )
ForceFieldSolvents=(spc     tip3p   tip3p   tip4p)
SolventFiles=(      spc216  spc216  spc216  tip4p)
ForceField=gromos45a3
SolModel=default
LIGANDS=()
VirtualSites=false


# System setup
PBCDIST=2.25
Salt=NA,CL
SaltCharge=1,-1
Salinity=0.1539976
CHARGE=
NDLP=false


# Simulation parameters
TIME=0               # Nanoseconds
AT=0.002              # Output frequency for positions, energy and log (ns)
Temperature=200,300  # Degree Kelvin
Tau_T=0.1            # ps
Pressure=1.01325     # Bar
Tau_P=0.5            # ps
PosreFC=200,200      # Position restraint force constant
Equi_time=0.010
Electrostatics=
RotationalConstraints=
SEED=$$


# GROUP DEFINITIONS
NATOMS=0
Biomol=()
Solute=()
Membrane=()
Solvent=()
Ligand=()
Ligenv=()
CoupleGroups=()
EnergyGroups=()
LIE=false


# User defined gromacs program options and simulation parameters (way flexible!)
PROGOPTS=()
MDPOPTS=()


OPTIONS=$(cat << __OPTIONS__

## OPTIONS ##

  File options:
    -f           Input coordinate file (PDB|GRO)                         *FILE:  None
    -name        Basename to use for files                               *STR:   Infer from input file 
    -top         Input topology (TOP)                                    *FILE:  None
    -fetch       Fetch file from PDB repository if not present           *BOOL:  False
    -l           Ligands to include (multiple instances allowed)
    -gmxrc       GMXRC file specifying gromacs locations                 *FILE:  $GMXRC
    -mdp         File with run parameters overriding internal ones       *FILE:  None

  Overall control options:
    -step        Step at which to start or resume the setup              *STR:   $STEP 
    -stop        Step at which to stop execution                         *STR:   $STOP
    -noexec      Do not actually simulate                                *BOOL:  False
    -force       Force overwriting existing files                        *BOOL:  False
    -archive     Archive results to file                                 *STR:   None
    -dir         Output directory                                        *STR:   $DIR
    -np          Number of processors/threads to use for MD run          *INT:   $NP
    -seed        Seed for random number generation                       *INT:   \$\$ 
    -mpi         prefix command for execution of mdrun                   *STR:   $MPI

  Simulation setup and parameters:
    -ff          Force field                                             *STR:   $ForceField
    -vsite       Use virtual sites                                       *BOOL:  False
    -solvent     Solvent model                                           *STR:   Infer from force field
    -elec        Treatment of electrostatic interactions (RF or PME)     *STR:   Infer from force field
    -t           Temperature                                             *FLOAT: $Temperature (K)
    -tau         Coupling time for temperature                           *FLOAT: $Tau_T (ps)
    -p           Pressure                                                *FLOAT: $Pressure (bar)
    -ptau        Coupling time for pressure                              *FLOAT: $Tau_P (ps)
    -d           Minimal distance between periodic images                *FLOAT: $PBCDIST (nm)
    -prfc        Position restraint force constant                       *FLOAT: $PRFC (kJ/mol/nm^2)
    -time        Simulation length in ns                                 *FLOAT: $TIME (ns)
    -at          Output resolution                                       *FLOAT: $AT (ns)
    -rtc         Use roto-translational constraints                      *BOOL:  False
    -ndlp        Perform simulations in a optimal (NDLP) simulation cell *BOOL:  False
    -lie         Calculate ligand (!) interaction energy                 *BOOL:  False

  Ions:
    -salt        Salt type (e.g. NA,CL or CU,2CL)                        *STR:   $Salt
    -sq          Ion charges                                             *STR:   $SaltCharge
    -charge      Charge to compensate (overrules charge of system)       *INT:   None
    -conc        Salt concentration in mol/l                             *FLOAT: $Salinity (M)
                 By default, counterions will be added. If the 
                 concentration is set negative, then salt is added 
                 without compensating for overall charge of the
                 system. Setting the concentration to -0 will 
                 disable addition of ions.

  Advanced control options

    $PROGRAM $VERSION allows specifying options for advanced control of 
    program invocation and simulation parameters. The former are given as

    --program-option=value

    This will add "-option value" to the command line of the call to 'program'.
    Note that this does not allow overriding options specified internally. 
    Trying to do so will result in an error due to double specification of the 
    option. If the option takes multiple arguments, then 'value' should be a 
    comma separated list.

    Simulation parameters can be set directly from the command line using

    --mdp-option=value

    This will add 'option = value' to the MDP file for all simulations 
    following energy minimization. MDP options specified on the command line
    take precedence over those specified in an input file (-mdp), which take
    precedence over parameters defined in this script. 
    The STEP/STOP controls can be used to set parameters for (pre)production
    simulations selectively.
    

__OPTIONS__
)


# Function for displaying USAGE information
USAGE ()
{
    cat << __USAGE__

$PROGRAM version $VERSION:

$DESCRIPTION

$OPTIONS

(c)$YEAR $AUTHORS
$AFFILIATION

__USAGE__
}


while [ -n "$1" ]; do
    case $1 in
	-h)     USAGE                                  ; exit 0 ;;
        # File options
	-f)       fnIN=$2                              ; shift 2; continue ;;
	-name)    NAME=$2                              ; shift 2; continue ;;
	-top)     TOP=$2                               ; shift 2; continue ;;
	-mdp)     MDP=$2                               ; shift 2; continue ;;
	-rtc)     RotationalConstraints=rtc            ; shift  ; continue ;;
	-ndlp)    NDLP=true; RotationalConstraints=rtc ; shift  ; continue ;;
	-step)    STEP=$2                              ; shift 2; continue ;;
	-stop)    STOP=$2                              ; shift 2; continue ;;
	-salt)    Salt=$2                              ; shift 2; continue ;;
	-conc)    Salinity=$2                          ; shift 2; continue ;;
	-sq)      SaltCharge=$2                        ; shift 2; continue ;;
	-charge)  CHARGE=$2                            ; shift 2; continue ;;
	-t)       Temperature=$2                       ; shift 2; continue ;;
	-ttau)    Tau_T=$2                             ; shift 2; continue ;;
	-p)       Pressure=$2                          ; shift 2; continue ;;
	-ptau)    Tau_P=$2                             ; shift 2; continue ;;
	-d)       PBCDIST=$2                           ; shift 2; continue ;;
	-prfc)    PosreFC=$2                           ; shift 2; continue ;;
	-time)    TIME=$2                              ; shift 2; continue ;;
	-at)      AT=$2                                ; shift 2; continue ;;
	-elec)    Electrostatics=$2                    ; shift 2; continue ;;
	-ff)      ForceField=$2                        ; shift 2; continue ;;
        -vsite)   VirtualSites=true                    ; shift  ; continue ;;
	-seed)    SEED=$2                              ; shift 2; continue ;;
	-dir)     DIR=$2                               ; shift 2; continue ;;
	-np)      NP=$2                                ; shift 2; continue ;;
	-solvent) SolModel=$2                          ; shift 2; continue ;;
	-archive) ARCHIVE=$2                           ; shift 2; continue ;;
	-force)   FORCE=true                           ; shift  ; continue ;;
        -noexec)  EXEC=echo                            ; shift  ; continue ;;
	-fetch)   FETCH=true                           ; shift  ; continue ;;
	-gmxrc)   GMXRC=$2                             ; shift 2; continue ;;
        -mpi)     MPI=$2                               ; shift 2; continue ;;
	-lie)     LIE=true                             ; shift  ; continue ;;
	-l)       LIGANDS[${#LIGANDS[@]}]=$2           ; shift 2; continue ;;
        --mdp-*)  MDPOPTS[${#MDPOPTS[@]}]=${1#--mdp-}  ; shift  ; continue ;;
	--*)      PROGOPTS[${#PROGOPTS[@]}]=$1         ; shift  ; continue ;;
	*)        
	    echo
	    echo "Unknown option "$1" found on command-line"
	    echo "It may be a good idea to read the usage:"
	    
	    USAGE

	    exit 1;;
    esac
done

echo $GMXRC

#--------------------------------------------------------------------
#---GROMACS STUFF
#--------------------------------------------------------------------

# Check and set the gromacs related stuff
if [[ -n $GMXRC && ! -f $GMXRC ]]
then
    echo GMXRC file specified, but not found \($GMXRC\)
    exit 1
elif [[ -z $GMXRC ]]
then
    [[ -f $SCRIPTDIR/GMXRC ]] && GMXRC=$SCRIPTDIR/GMXRC || GMXRC=`which GMXRC`
fi

# Source the gromacs RC file if one was found
[[ -n $GMXRC ]] && source $GMXRC 

#export GMXLIB=$GMXDATA/top
#echo $GMXLIB

#if [[ -n $MPI ]]
#   then
#   export GMXLIB=$GMXDATA/gromacs/top
#fi

# Check whether grompp and mdrun are executable
# If they are not, attempt to make them so
# (This may be required for Grid processing)
[[ -x $GMXBIN/grompp ]] || chmod +x $GMXBIN/grompp
[[ -x $GMXBIN/mdrun  ]] || chmod +x $GMXBIN/mdrun


#--------------------------------------------------------------------
#---INITIAL CHECKS AND LOGGING
#--------------------------------------------------------------------


## 1. Expand options that can take multiple, comma-separated values

# This concerns options for equilibration, such as temperature,
# pressure and position restraint force constants. These will
 # be used to set up cycles of equilibration. Position restraints Fc
# and temperature are cycled together in STEP 6 (NVT), followed by 
# pressure equilibration in STEP 7 (NPT).

# Store the Internal Field Separator (IFS)
ifs=$IFS
IFS=","
Temperature=($Temperature)
Tau_T=($Tau_T)
Pressure=($Pressure)
Tau_P=($Tau_P)
PosreFC=($PosreFC) 
Salt=($Salt)
SaltCharge=($SaltCharge)
# Restore the field separator
IFS=$ifs


## 2. Echo options for direct modulation of program calls

# These options are formatted like --program-option=value
# This will add '-option value' on the command line of the 
# specific program. If an option takes multiple arguments
# then these should be given comma separated. The commas 
# will be replaced by spaces.
# *NOTE*: Some options are defined internally and can not be 
# overriden. Attempting to do so will result in an error, as
# options will be doubly specified.

if [[ -n $PROGOPTS ]]
then
    echo Program options specified on command line:
    for ((i=0; i<${#PROGOPTS[@]}; i++)); do echo ${PROGOPTS[$i]}; done
    echo ===
fi


## 3. Echo mdp options specified on the command line

# These options are formatted like --mdp-param=value
# This will add 'param = value' to the MDP file for 
# all runs following energy minimization. 
# *NOTE*: Options specified on the command line take
# precedence over internal parameters and over those
# read from an mdp file, provided as value to option
# -mdp 

if [[ -n $MDPOPTS ]]
then
    echo 'Simulation parameters specified on command line (note how flexible!):'
    for ((i=0; i<${#MDPOPTS[@]}; i++)); do echo ${MDPOPTS[$i]}; done
    echo ===
fi


#--------------------------------------------------------------------
#---WARMING UP VARIABLE GYMNASTICS
#--------------------------------------------------------------------

# Parse input file names - expand to full path
pdb=${fnIN##*/}                                  # Filename
dirn=$(cd ${fnIN%${fnIN##*/}}./; pwd)            # Directory
base=${pdb%.*}                                   # Basename
ext=${pdb##*.}                                   # Extension
[[ -n $fnIN ]] && fnIN=$dirn/$pdb
topdir=$(cd ${TOP%${TOP##*/}}./; pwd)
[[ -n $TOP ]]  && TOP=$topdir/${TOP##*/}
[[ -n $NAME ]] && base=$NAME  # Override base name if name is given
# Base directory from which command was given
BDIR=$(pwd)

echo Input file:       $pdb
echo Base name:        $base
echo Source directory: $dirn

if [ $dirn != $BDIR ]
then
  echo "WARNING: The run will be performed in this directory (`pwd`), while the input file is in another ($dirn). This could of course be intended."
fi


# Change working directory, creating one if necessary
[[ ! -d $DIR ]] && mkdir -p $DIR; cd $DIR


# Copy topology stuff if we specify a topology
[[ -n $TOP ]] && cp $topdir/*itp ./


# Set a trap for signals
archive ()
{
    if [[ -n $ARCHIVE ]]
    then
	tar cfz $ARCHIVE.tmp.tgz `ls --ignore=$ARCHIVE`
	mv $ARCHIVE.tmp.tgz $ARCHIVE
    fi
}
trap "archive" 2 9 15


# Set the forcefield tag
case $ForceField in
    gromos*) ForceFieldFamily=gromos;;
    amber*)  ForceFieldFamily=amber;;
    charmm*) ForceFieldFamily=charmm;;
    opls*)   ForceFieldFamily=opls;;
esac


# Set the solvent model
if [[ $SolModel == default ]]
then
    # Get the right solvent model for the force field selected
    for ((i=0; i<${#ForceFieldFamilies[@]}; i++))
    do
	if [[ $ForceFieldFamily == ${ForceFieldFamilies[$i]} ]]
	then
	    SolModel=${ForceFieldSolvents[$i]}
	fi
    done
fi


# Set the starting/stopping step
# Step up to the step-in step
for ((i=0; i<${#STEPS[@]}; i++)); do [[ ${STEPS[$i]} == ${STEP}* ]] && STEP=$i && break; done
# Step up to the stop-step: stop if the step stepped up to is the step to stop at
for ((i=0; i<${#STEPS[@]}; i++)); do [[ ${STEPS[$i]} == ${STOP}* ]] && STOP=$i && break; done


# Remove flags from previous runs
[[ -e DONE  ]] && rm DONE
[[ -e ERROR ]] && echo Found ERROR flag, probably from previous run. Trying again. && rm ERROR


#--------------------------------------------------------------------
#---INFORMATIVE OUTPUT--          
#--------------------------------------------------------------------

echo Starting MD protocol for $fnIN

echo Using $ForceFieldFamily force field $ForceField with $SolModel water model

[[ -n $Electrostatics ]] \
    && echo Using $Electrostatics for treatment of long range coulomb interactions \
    || echo Inferring electrostatics treatment from force field family \(check mdp files\)

$VirtualSites \
    && echo Using virtual sites \
    || echo Not using virtual sites

$NDLP \
    && echo Simulations will be performed using a near-densest lattice packing unit cell \
    || echo Simulations will be performed in a rhombic dodecahedron unit cell 


#--------------------------------------------------------------------
#---SIMULATION PARAMETERS--          
#--------------------------------------------------------------------

## OT N ## For every parameter not defined the default is used
## NOTE ## This is probably fine for equilibration, but check the defaults to be sure
## E OT ## The list as is was set up for gromacs 4.5

# This function lists the mdp options requested based on a preceding tag
mdp_options ()
{    
    for tag in $@
    do
	# Find variables declared with specified tag
        for opt in `set | grep ^__mdp_${tag}__`
        do
	    # Strip everything from the first = to the end 
	    # to get the variable name
            var=${opt%%=*}
	    # Strip everything up to the first = to get
	    # the value
            val=${opt#*=}
	    # Replace the tag and redeclare in local space
	    # If the variable was already declared it will
	    # be overridden.
            local ${var/mdp_$tag/mdp}=$val
        done
    done
    # Find all variables starting with __mdp__ and echo them
    set | $SED -n '/^__mdp__/{s/__mdp__//;s/,/ /g;p;}'
}


#--------------------------------------------------------------------
# Global parameters

__mdp_md__dt=0.002
__mdp_md__nstlist=4

# Virtual site specific
if $VirtualSites; then
  __mdp_md__dt=0.004
  __mdp_md__lincsorder=4
  __mdp_md__nstlist=2
fi

# Output parameters
TIME=$(python -c "print int(1000*$TIME/$__mdp_md__dt + 0.5 )") 
AT=$(python -c "print int(1000*$AT/$__mdp_md__dt + 0.5)") 
__mdp_md__nsteps=$TIME
__mdp_md__nstxout=$AT
__mdp_md__nstvout=0 
__mdp_md__nstfout=0
__mdp_md__nstlog=$AT
__mdp_md__nstenergy=$AT
__mdp_md__nstxtcout=0

# Coupling
# Listed here are the overall controls. Specific controls
# (temperature,pressure,time constants) are controlled through
# the command line interface and taken care of in steps 6/7
# The temperature is set later on
__mdp_md__tcoupl=Berendsen
__mdp_md__nsttcouple=$__mdp_md__nstlist
__mdp_md__nstpcouple=$__mdp_md__nstlist
__mdp_md__compressibility=4.5e-5

# Nonbonded interactions
__mdp_md__coulombtype=PME
__mdp_md__fourierspacing=0.125
__mdp_md__rcoulomb=0.9
__mdp_md__rlist=0.9
__mdp_md__rvdw=0.9
__mdp_md__pme_order=4
__mdp_md__ewald_rtol=1e-5

# Other
__mdp_md__constraints=all-bonds
__mdp_md__comm_mode=Linear
__mdp_md__comm_grps=System
__mdp_md__nstcomm=$__mdp__nstlist


#--------------------------------------------------------------------
# Rotational constraints

__mdp_rtc__comm_mode=RTC
__mdp_rtc__comm_grps=Solute

#--------------------------------------------------------------------
# Force field specific parameters

# AMBER, all versions: default is default

# GROMOS96, all versions
__mdp_gromos__coulombtype=Reaction-Field
__mdp_gromos__rcoulomb=1.4
__mdp_gromos__epsilon_rf=61
__mdp_gromos__rvdw=1.4

# CHARMM
__mdp_charmm__coulombtype=Switch
__mdp_charmm__rcoulomb_switch=1.0
__mdp_charmm__rcoulomb=1.2
__mdp_charmm__vdwtype=Switch
__mdp_charmm__rvdw_switch=1.0
__mdp_charmm__rvdw=1.2

# OPLS/AA
__mdp_opls__coulombtype=Cut-off
__mdp_opls__rcoulomb=1.4

#--------------------------------------------------------------------
# Energy minimization

__mdp_em__define=-DPOSRES
__mdp_em__integrator=steep
__mdp_em__nsteps=20
__mdp_em__pbc=no
__mdp_em__rlist=0.9
__mdp_em__rcoulomb=1.4
__mdp_em__rvdw=1.4
__mdp_em__nstlist=1
__mdp_em__constraints=none
__mdp_em__constraint_algorithm=Lincs
__mdp_em__lincs_order=4


#--------------------------------------------------------------------
# Equilibration runs: position restraints, NVT, NPT

# Position restraints are relieved at step 7
__mdp_equil__define=-DPOSRES
__mdp_equil__dt=0.002
__mdp_equil__nstlist=4
__mdp_equil__nsttcouple=1
__mdp_equil__nstlog=0
__mdp_equil__nstenergy=0
__mdp_equil__nstxtcout=0

# Velocities are only generated once
# After the first NVT/PR cycle 'genvel' is set to no
# and the other two options are ignored
__mdp_equil__genvel=yes
__mdp_equil__gen_seed=$SEED
__mdp_equil__gen_temp=${Temperature[0]}

#--------------------------------------------------------------------
# User specified parameters
# These will be used in PR-NVT, PR-NPT, MD-INIT, MD-PRE and MD
# To specify parameters for a single step, make cunning use of
# -step and -stop.

if [[ -n $MDP ]]
then
    # Check if the MDP file specified exists and exit if not
    [[ ! -f $MDP ]] && echo "MDP file $MDP specified, but not found" && exit
    
    # Gather options
    # 1. Delete empty lines
    # 2. Delete comment lines
    # 3. Remove whitespace on either side of the equality sign
    # 4. Remove trailing whitespace
    # 5. Replace spaces with commas
    USER_MDP=( $( $SED '/^ *$/d;/^ *;/d;s/\s*=\s*/=/;s/\s*$//;s/ /,/g' $MDP ) )
    
    for i in ${USER_MDP[@]}
    do 
	opt=${i%%=*}
	val=${i#$opt}
	eval "__mdp_usr__${opt//-/_}$val"
    done    
fi

if [[ -n $MDPOPTS ]]
then
    for i in ${MDPOPTS[@]}
    do
        # --mdp-energygrps=bla,bla,bla
        opt=${i%%=*}
        val=${i#$opt}
        eval "__mdp_usr__${opt//-/_}$val"
    done
fi

#--------------------------------------------------------------------

#--------------------------------------------------------------------
#---SUBROUTINES--
#--------------------------------------------------------------------


ERROR=0

exit_clean()
{
    [[ -f RUNNING ]] && rm -f RUNNING

    touch DONE

    echo Deleting redundant files:
    printf "%-25s %-25s %-25s %-25s %-25s\n" ${JUNK[@]} \#*\#
    for i in ${JUNK[@]} \#*\#; do [[ -f $i ]] && rm $i; done

    exit 0
}

exit_error()
{

  echo "**"
  echo "** Something went wrong in running script $PROGRAM from"
  echo "** `pwd`/:"
  echo "**"
  echo "** exit code: $1"
  echo "** $MSG"
  echo "**"

  [[ -f RUNNING ]] && rm -f RUNNING
  touch ERROR

  archive

  exit 1
}

# Trashing files
trash()
{
    for item in $@; do JUNK[${#JUNK[@]}]=$item; done
}

# Routine for gathering program specific options
program_options()
{    
    local OPTS=
#    for opt in ${PROGOPTS[@]}
#    do
#	if [[ $opt =~ --$1 ]]
#	then
#            OPTS="$OPTS $( $SED 's/--[^-]*//;s/=/ /' <<< $opt)"
#	fi
#    done
    for ((opt = 0; opt < ${#PROGOPTS[@]}; opt++))
    do
        if [[ ${PROGOPTS[$opt]} =~ --$1 ]]
        then
            OPTS="$OPTS $( $SED 's/--[^-]*//;s/=/ /' <<< ${PROGOPTS[$opt]} )"
        fi
    done
    echo $OPTS
}

# Check for the existence of all arguments as files
all_exist()
{
  for f in ${OUTPUT[@]} 
  do 
      [[ -e $f ]] || return 1
  done
}

# This is a function to generate a sequence of numbers
# On Linux platforms there usuallye is 'seq', but we 
# can not depend on it.
SEQ(){ for ((i=$1;i<=$2;i++)); do echo $i; done };

# Routine for generating a simple index file
INDEX ()
{
  [[ -n $2 ]] && fn=$2 || fn=basic.ndx

  exec 6>&1 && exec >$fn

  fmt="%5d %5d %5d %5d %5d %5d %5d %5d %5d %5d"

  # Total number of atoms
  N=$( $SED -n '2{p;q;}' $1)
  echo "[ System ]"
  printf "$fmt\n" `SEQ 1 $N` | $SED 's/ 0//g'
  
  # Solvent atoms (including ions, etc, listed after 'SOL')
  SOL=$(( $( $SED -n '/SOL/{=;q;}' $1) - 2 ))
  echo "[ Solvent ]"
  printf "$fmt\n" `SEQ $SOL $N` | $SED 's/ 0//g'

  # Base system: solute and membrane, if present
  echo "[ Base ]"
  printf "$fmt\n" `SEQ 1 $((SOL - 1))` | $SED 's/ 0//g'

  # Membrane, if any
  MEMBRANE=$( $SED -n '/\(POP\|DPP\|DMP\|DOP\|PPC\)/{=;q;}' $1)
  if [[ -n $MEMBRANE ]]
  then
      echo '[ Membrane ]'
      printf "$fmt\n" `SEQ $MEMBRANE $((SOL - 1))` | $SED 's/ 0//g'
  else
      MEMBRANE=SOL
  fi

  echo '[ Solute ]'
  printf "$fmt\n" `SEQ 1 $((MEMBRANE - 1))` | $SED 's/ 0//g'

  exec 1>&6 6>&-

  return 0
}

MDRUNNER ()
{
    local NP=1
    local fnOUT=
    local fnNDX=
    local FRC=false
    local SPLIT=
    local SINGPROC=
    while test -n "$1"; do
	case $1 in
	    -f)     local fnMDP=$2        ; shift 2; continue;;
            -c)     local  fnIN=$2        ; shift 2; continue;;
	    -n)     local fnNDX=$2        ; shift 2; continue;;
            -o)     local fnOUT=$2        ; shift 2; continue;;
	    -p)     local fnTOP=$2        ; shift 2; continue;;
	    -l)     local fnLOG=$2        ; shift 2; continue;;
	    -force) local   FRC=$2        ; shift 2; continue;;
	    -np)    local    NP=$2        ; shift 2; continue;;
	    -onepr) local  SINGPROC=-pd   ; shift  ; continue;;
	    -split) local SPLIT=-noappend ; shift  ; continue;;
            *)  echo "PANIC!: Internal Argument Error ($1) in routine MDRUNNER"; exit;;
        esac
    done


    # Check input
    [[ -f $fnIN  ]] || exit_error ${STEP}1
    [[ -f $fnTOP ]] || exit_error ${STEP}2
    [[ -n $fnNDX && -f $fnNDX ]] || INDEX $fnIN $fnNDX


    # Infer basename from output file name
    baseOUT=${fnOUT%.*}


    # Check if there are parts of runs
    if [[ -n $SPLIT ]]
    then
	# A neat way to check for the last of a set of numbered files
	# The work is done in the while test, incrementing the number 
	# before checking if the file exists. The statement is empty 
	# (using the true command ':'). The while loop ends with z being
	# equal to the first number not used.
	local z=0; while [[ -f $baseOUT.part$(printf "%04d" $((++z))).log ]]; do :; done
	# The last existing file has number one less than z
	last=$baseOUT.part$(printf "%04d" $((z-1))).log
	# The logfile to write 
	log=$baseOUT.part$(printf "%04d" $z).log
    else	
	log=$baseOUT.log 
	last=$log
    fi


    # Check whether the log file actually exists
    step=0
    if [[ -e $last ]]
    then
        # Get the last Step/Time/Lambda listed in the last log file
        # Nifty: At each line containing Step/Time/Lambda, 
        # read a next line (n) and put it in the hold space (h)
        # At the end of the file, switch the hold space and the 
        # pattern space (x) and print (p)
	step=($( $SED  -n -e '/^ *Step *Time *Lambda/{n;h}' -e '${x;p}' $last))
    fi
	

    # Check whether we need to do anything
    if $FRC
    then
	removed=()
	for z in ${baseOUT}.*; do [[ -f $z ]] && rm $z && removed[${#removed[@]}]=$z; done
	echo Forced execution. Removed files:
	echo ${removed[@]}
    elif [[ -f $fnOUT ]]
    then
	echo Output found \($fnOUT\). Skipping step ${STEPS[$STEP]}
	return 0
    elif [[ $step -gt $TIME ]]
    then
	echo A log file exists which reports having run $step of $TIME steps \($last\)
	return 0
    fi


    # Set the options for the parameter and index files
    fnMDP="-f $fnMDP -po ${fnMDP%.mdp}-out.mdp"
    [[ -n $fnNDX ]] && fnNDX="-n $fnNDX"


    # Skip generation of run input file if it exists
    if [[ ! -e $baseOUT.tpr ]]
    then
	GROMPP="$GMXBIN/grompp $fnMDP -c $fnIN -p $fnTOP $fnNDX -o $baseOUT.tpr $(program_options grompp)"
	echo $(date): $GROMPP | tee $fnLOG
	$GROMPP >>$fnLOG 2>&1 || exit_error ${STEP}3
    fi


    # If the output file extension is 'tpr' we should be done here
    [[ ${fnOUT#$baseOUT} == .tpr ]] && return 0


    # If we extend a partial run, mention it
    [[ ! -e $fnOUT && -e $baseOUT.cpt ]] && echo $(date): FOUND PARTIAL ${STEPS[$STEP]} RESULTS... CONTINUING


    # Run the run
#    MDRUN="$GMXBIN/mdrun -nice 0 -deffnm $baseOUT -c $fnOUT -cpi $baseOUT.cpt -nt $NP $SPLIT $(program_options mdrun)"
    MDRUN="$MPI $GMXBIN/mdrun -nice 0 -deffnm $baseOUT -c $fnOUT -cpi $baseOUT.cpt $SINGPROC $SPLIT $(program_options mdrun)"
    echo $(date): $MDRUN | tee -a $fnLOG
    $MDRUN >>$fnLOG 2>&1 || exit_error ${STEP}4


    # If we split then we have to do some more work to see if we have finished
    if [[ -n $SPLIT ]]
    then
	STEP=( $SED -n -e '/Step *Time *Lambda/{n;h}' -e '${x;p}' $fnLOG)
	[[ $STEP == $FIN ]] && cp ${fnLOG%.log}.gro $fnOUT
    fi

    
    # If $fnOUT exists then we finished this part
    if [[ -e $fnOUT ]]
    then
	echo $(date): FINISHED MDRUN ${STEPS[$STEP]} | tee -a $fnLOG
	return 0
    else
	echo $(date): MDRUN ${STEPS[$STEP]} EXITED, BUT RUN NOT COMPLETE | tee -a $fnLOG
	return 1
    fi
}

# Macro to echo stuff only if the step is to be executed
ECHO() { [[ $STEP == $NOW ]] && echo "$@"; }

# Macro to do stuff only if the step is to be executed
DO() { [[ $STEP == $NOW ]] && echo $@ && $@; }


#--------------------------------------------------------------------
echo "#---= THIS IS WHERE WE START =--"
#--------------------------------------------------------------------

NOW=0


# Check whether the file exists
if $FETCH && [[ ! -f $dirn/$pdb ]] 
then
    # Try fetching it from the PDB
    wget www.rcsb.org/pdb/files/$base.pdb.gz
    pdb=$base.pdb.gz
    ext=gz
fi


# Allow feeding zipped files - temporarily unzipping them
if [[ $ext == gz ]]
then
    gz=$pdb
    pdb=$base
    [[ -z $NAME ]] && base=${base%.*}
    gunzip -c $gz > $pdb && trash $pdb
fi


# If we are at this step, but have a top file already, increase the STEP
if [[ $STEP == $NOW && -n $TOP && -n $fnIN ]]
then
    echo 'creation structure'
   echo $GMXLIB
    # If the accompanying GRO file does not exist, convert the PDB file
    [[ -e $base.gro ]] || editconf -f $fnIN -o $base.gro
    : $(( STEP++ ))
fi


# If we do not have an input file, definitely skip the first step
# This may happen if we set up a ligand-in-solvent simulation, or
# just a box of solvent, or maybe a membrane...
[[ $STEP == $NOW && -z $fnIN ]] && : $((STEP++))


#--------------------------------------------------------------------
ECHO "#---STEP 1A: GENERATE STRUCTURE AND TOPOLOGY FOR INPUT PDB FILE"
#--------------------------------------------------------------------

# Output for this section:
OUTPUT=($base.top $base.gro)


# Delete existing output if we force this step
[[ $STEP == $NOW ]] && $FORCE && rm ${OUTPUT[@]}


# If we are here now, we should generate a top file
[[ $STEP == $NOW ]] && TOP=$base.top


## I. Build command 


# 1. Basic stuff
PDB2GMX="$GMXBIN/pdb2gmx -v -f $dirn/$base.pdb -o $base.gro -p $base.top -ignh -ff $ForceField -water $SolModel"


# 2. Position restraints
#    * The position restraint fc (-posrefc) is bogus and 
#      intended to allow easy replacement with sed.
#      These will be placed under control of a #define
PDB2GMX="$PDB2GMX -i $base-posre.itp -posrefc 999"


# 3. Virtual sites
$VirtualSites && PDB2GMX="$PDB2GMX -vsite hydrogens" 


# 4. Add program options specified on command line (--pdb2gmx-option=value)
PDB2GMX="$PDB2GMX $(program_options pdb2gmx)"


# 5. Specification of protonation states
if [[ $STEP == $NOW ]]
then
    if [[ -e $dirn/$base.tit || -e $dirn/titratables.dat ]]
    then
	[[ -e $dirn/$base.tit ]] && TITR=$base.tit || TITR=titratables.dat
	echo SETTING PROTONATION STATES FROM $dirn/$TITR
        # Acidic residues ASP and GLU: deprotonated=0 protonated=1
	ACID='/\(ASP\|GLU\)/{s/.*[Hh0]\s*$/1/;s/.*\-\s*/0/}'
        # Basic residue LYS: deprotonated=0 protonated=1
	LYS='/LYS/{s/.*0\s*$/0/;s/.*[Hh+]\s*$/1/}'
        # Histidine: 
	HIS='/HIS/{s/.*[DdAa]\s*$/0/;s/.*[EeBb]\s*$/1/;s/.*[Hh\+]\s*$/2/}'
        # N-terminal
	NTER='/NTER/{s/.*\+\s*$/0/;s/.*0\s*$/1/;s/.*N\s*/2/}'
        # C-terminal
	CTER='/CTER/{s/.*\-\s*$/0/;s/.*0\s*$/1/;s/.*N\s*/2/}'
	
	$SED -e "$ACID" -e "$LYS" -e "$HIS" -e "$NTER" -e "$CTER" $dirn/$TITR > pdb2gmx.query
	trash pdb2gmx.query
    fi
    
    if [ -e "$dirn/pdb2gmx.query" ]; then
	GMXQUERY=$(cat $dirn/pdb2gmx.query)
	PDB2GMX="$PDB2GMX -ter -lys -asp -glu -his"
    else
	GMXQUERY=
    fi
fi


## II. Process (or not)


# Skipping because of existing output
if [[ $STEP == $NOW ]] && $(all_exist ${OUTPUT[@]})
then
    echo "Output found, skipping topology generation" 
    : $((STEP++))
fi


# Skipping verbosely; showing what would have been run
if [[ $STEP == $NOW && -n $EXEC ]]
then
    echo "Skipping: $PDB2GMX"
    : $((STEP++))
fi


# Execute
if [[ $STEP == $NOW ]]
then
    LOG=01-PDB2GMX.log

    echo `date`: $PDB2GMX | tee -a $LOG
    echo $GMXQUERY | $PDB2GMX >>$LOG 2>&1 || exit_error 1

    NATOMS=$( $SED -n '2{p;q;}' $base.gro)

    for itp in ${base}-posre*.itp
    do
        $SED -i -e '1i#ifndef HPOSCOS\n  #define HPOSCOS 200\n#endif' \
            -e 's/999 \+999 \+999/HPOSCOS HPOSCOS HPOSCOS/' $itp
    done

    # Simplify topology if identical chains are found
    # First get the list of moleculetype itp files
    ITP=(${base}_*.itp)

    # Extract the moleculetype names from the itp files
    # - at the line matching 'moleculetype'
    # - set a label
    # - read in a new line and branch back if the line is a comment
    # - if it is not a comment get the first word, print it, and quit  
    MTP=($(for i in ${ITP[@]}; do [[ -e $i ]] && $SED -n '/moleculetype/{:a;n;/^;/ba;s/\s\+.*$//p;q}' $i; done))

    # Compare each pair of itp files
    for ((i=1; i<${#ITP[@]}; i++))
    do
	for ((j=0; j<$i; j++))
	do
	    # Check how many lines are different, excluding includes and comments
	    # For identical moleculetypes only the moleculetype name should differ
	    # That will give four lines of output from diff
	    if [[ $(diff -I "^\(;\|#include\)" ${ITP[$i]} ${ITP[$j]} | wc -l) == 4 ]]
	    then
		echo Removing duplicate moleculetype definition in ${ITP[$i]}
		# 1. remove the #include statement for that itp file
		# 2. rename the moleculetype under [ system ]
		$SED -i -e "/${ITP[$i]}/d" -e "/[\s*system\s*]/,\$s/${MTP[$i]}/${MTP[$j]}/" $base.top
		# List the file for removal
		trash ${ITP[$i]} $( $SED 's/_/-posre_/' <<< ${ITP[$i]})
		
		break
	    fi
	done
    done	

    
    # Set the topology to the newly generated one
    TOP=$base.top
fi


## BOOKKEEPING ##

# Bookkeeping is always done, also if the step is not executed #

# Index groups, Coupling Groups, Energy Groups
if [[ -e $base.gro ]]
then
    NATOMS=$( $SED  -n '2{p;q;}' $base.gro)

    # Set the solute start and end atom:
    Biomol=(1 $NATOMS)

    # Set the solute start and end atom:
    Solute=(1 $NATOMS)

    # If we add ligands, the solute is also in the ligand environment
    Ligenv=(1 $NATOMS)

    # List the solute as coupling group and as energy group
    CoupleGroups=(Solute)
    EnergyGroups=(Solute)
fi


# If we have a gro file here, it is named $base.gro.
# We won't have one if we did not have an input file,
# like when setting up a box of solvent
[[ -n $fnIN ]] && GRO=$base.gro || GRO=


# End of step
[[ $STOP ==   $NOW     ]] && exit_clean
[[ $STEP == $((NOW++)) ]] && : $((STEP++))


#--------------------------------------------------------------------
ECHO "#---STEP 1B: ADD LIGANDS SPECIFIED ON COMMAND LINE"
#--------------------------------------------------------------------

# ADD LIGANDS


# Skip this step if there are no ligands to add
[[ $STEP == $NOW && ${#LIGANDS[@]} == 0 ]] && : $((STEP++))


# Output for this section:
OUTPUT=($base-lig.top $base-lig.gro)


# Delete existing output if we force this step
[[ $STEP == $NOW ]] && $FORCE && rm ${OUTPUT[@]}


# Check output
if [[ $STEP == $NOW && $(all_exist ${OUTPUT[@]}) ]]
then
    echo Found output... Skipping addition of ligand\(s\).
    : $((STEP++))
fi


# Execute this step
if [[ $STEP == $NOW && ${#LIGANDS[@]} -gt 0 ]]
then
    echo Adding Ligands


    ## 1. Input GRO file

    # This step requires a GRO file, but we allow stepping in with a
    # PDB file, as long as the TOP file is present. The PDB file is
    # then converted to GRO format here.
    [[ -z $GRO && -f $pdb ]] && editconf -f $pdb -o $base.gro

    # If $GRO is not set here, it must be $base.gro
    # This can also be written GRO=${GRO:-$base.gro}
    [[ -z $GRO ]] && GRO=$base.gro


    ## 2. Setting up coordinate file containing ligands

    #     Overwrite the file if it already exists.
    #     a. Retain title
    #        Here we use a trick to write the title of the new .gro file.
    #        If we already have $GRO the first line is copied,
    #        otherwise a new line is written. To make sure that whichever
    #        goes to standard out and into the new file, the commands are 
    #        grouped together, using curly braces. Mind the semicolon.
    #        The redirect captures the stdout of the compound command.
    { [[ -f $GRO ]] && head -1 $GRO || echo Ligand; } > $base-lig.gro

    #     b. Note the current number of atoms
    #           Again, base the results on the existence of $base.gro
    
    [[ -f $GRO ]] && natoms=`$SED -n '2{p;q;}' $GRO` || natoms=0

    #     c. Store the line number of the box definition
    box=$((natoms+3)) 
    
    #     d. Write the coordinates to the new file, if there are any
    [[ $natoms -gt 0 ]] && $SED -ne "3,$((natoms+2))p" $GRO >> $base-lig.gro


    ## 3. Listing of ligands

    #     a. Moleculetype names listing
    mols=()
    
    #     b. Moleculetype definitions
    itps=()

    #     c. Add ligand coordinates to the structure file
    #
    #        Ligands are specified like:
    #
    #            -l structure[,topology[,name]]
    #
    #        The structure file should contain the coordinates
    #        for a single ligand. The topology file should 
    #        contain a [ moleculetype ] definition of the ligand,
    #        but may be omitted if the definition is already available,
    #        e.g. from the default libraries or from a definition in the
    #        master topology file. 
    #        If no file is specified containing the moleculetype 
    #        definition, then the moleculetype name can be specified.
    #        Otherwise, the name is set to the residuename of the first 
    #        atom. 
    #
    for lig in ${LIGANDS[@]}
    do
	# The ligand specification must contain a coordinate file.
	# Split the structure file name from the rest.
	struc=${lig%%,*}
	rest=${lig#$struc}

	# Check the file format and convert to GRO if necessary.
	if [[ ${struc%.gro} == $struc ]]
	then
	    [[ ! -e $struc.gro ]] && editconf -f $struc -o $struc.gro >/dev/null 2>&1
	    struc=$struc.gro
	    trash $struc
	fi

	# Get the atom count for the ligand
	latoms=$( $SED  -n '2{p;q;}' $struc)

	# Add the atoms to the GRO file
	$SED -n 3,$((latoms+2))p $struc >> $base-lig.gro

	# Add the number to the total
	: $((natoms += latoms))

	mtd=
	# Check whether there is more
	if [[ -z $rest ]]
	then
	    # If nothing else is specified, take the name from the
	    # residue name of the first atom in the GRO file
	    # (the characters five to ten on the line).
	    lname=$( $SED  -n '3{s/^.....\(.....\).*/\1/p;q;}' $struc)
	else
	    # Take off the preceding comma
	    rest=${rest#,}
	    # Check what is given: try to take off whatever matches
	    # up to and including the first comma (may be nothing)
	    lname=${rest#*,}
	    rest=${rest%$lname}
	    # If there is a rest still, then it should be a file
	    # with a moleculetype definition (mtd)
	    # Otherwise lname contains a filename or the molecule name	    
	    if [[ -n $rest ]]
	    then
		mtd=${rest%,}
	    elif [[ -e $lname ]]
	    then
		mtd=$lname
		# Extract the first moleculetype name
		lname=($( $SED -n '/moleculetype/{:a;n;/^ *[^;]/{p;q};ba}' $mtd))
	    fi
	fi

	# Add the ligand name to the list
	mols[${#mols[@]}]=$lname

	# Add the file containing the definition to the list
	[[ -n $mtd ]] && itps[${#itps[@]}]=$mtd
    done

    
    ## 4. Finalize GRO file

    #     a. Add the original box definition
    
    { [[ -f $GRO ]] && $SED -ne "${box}p" $GRO || echo 0 0 0; } >> $base-lig.gro
    #     b. Update the atom count on the second line
    $SED -i "2i$(printf %5d $natoms)" $base-lig.gro
    
    ## 5. Topology

    #     a. Set up the topology file containing ligands
    #        adding #include statements before [ system ] directive
    if [[ -n $TOP ]]
    then
	# We already have a topology.
        # First copy the topology up to [ system ]:
        #  * Suppress printing (not to print the directive)
        #  * At the directive, quit
        #  * Otherwise, print the line
  $SED -n "/^\[ system \]/q;p;" $TOP > $base-lig.top
    else
	# We don't have a topology yet.
	# Build one!
	echo -e "#include \"$ForceField.ff/forcefield.itp\"\n#include \"$SolModel.itp\"" > $base-lig.top
    fi

    #     b. Add include statements for ligands. Only add each file once
    #        Use $SED to replace spaces by newlines, and feed the results 
    #        to 'sort -u' to uniqify. Loop over the resulting entries, 
    #        #including each in the topology 
    for mtd in $( $SED  's/ /\n/g' <<< ${itps[@]} | sort -u); do echo "#include \"$mtd\""; done >> $base-lig.top
#    echo "crea ligando"
#    echo $mtd
#    fake999=`echo $itps | $SED 's#/#\n#g' | $SED 's#\.#\n#g'`
#    fake998=($fake999)
#    posre=`echo $mtd | $SED 's#.itp#-posre.itp#g'`
#    pref=${fake998[$(( ${#fake998[@]} -2 ))]}


#    estensione=${fake998[$(( ${#fake998[@]} -1 ))]}
#    copia=`echo $mtd | $SED 's/\.'$estensione'/\*/g'`
    # remove the atomtype definition from the itp created by acepyp
#    awk 'BEGIN{scrivi=0}{if (($0 ~ /\[/ ) && ($2 == "atomtypes" )) {scrivi=1} else if (($0 ~ /\[/ ) && ($2 != "atomtypes" )) {scrivi=0} if ((scrivi==0)) {printf "%s\n",$0}}' $mtd > ./${pref}.itp
#      echo -e "#ifdef POSRES\n#include \"${pref}-posre.itp\"\n#endif" >> ./${pref}.itp
#    awk 'BEGIN{scrivi=0}{if (($0 ~ /\[/ ) && ($2 == "atomtypes" )) {scrivi=1} else if (($0 ~ /\[/ ) && ($2 != "atomtypes" )) {scrivi=0} else if (!($0 ~ /\[/ ) && (scrivi==1) && ($1!="nc") && ($1!="cg") && ($1!="cd") && ($1!="nd") && ($1!="fe") && ($1!="c3")) {printf "%s\n",$0}}' $mtd  >> ./attypes.itp
#      cp $posre ./

#      echo "#include \"${pref}.itp\"" >> $base-lig.top

    #     c. Add the original system definition (after adding a newline)
    echo >> $base-lig.top
    if [[ -n $TOP ]]
    then
        # i.  Print from the [ system ] directive up to and including the [ molecules ] directive
	EXPR1='/^\[ *system *\]/,/^\[ *molecules *\]/p' 
        # ii. At the [ molecules ] directive, start a loop to stop at the first blank line (:a ... ba)
        #     In the loop:
        #      * Read in newline (n)
        #      * Check if it is blank, and quit if so (/^ *$/q;)
        #      * Otherwise print the line (p) and branch back to the label (ba)
	#     NOTE: MOLECULES ARE ONLY ADDED IF WE ALREADY HAD AN INPUT STRUCTURE
  [[ -f $GRO ]] && EXPR2='/^\[ *molecules *\]/{:a;n;/^ *$/q;p;ba}' || EXPR2=""
	$SED -n -e "$EXPR1" -e "$EXPR2" $TOP >> $base-lig.top
    else
	echo -e '[ system ]\nLigand in solvent\n\n[ molecules ]' >> $base-lig.top
    fi

    #     d. Then add the molecule list for the ligands
    #        Add specifications of identical molecules together
    mols=( $( $SED  's/ /\n/g' <<< ${mols[@]} | uniq -c) )
    for ((i=1; i<${#mols[@]}; i+=2)); do printf "%-5s %10d \n" ${mols[$i]} ${mols[$((i-1))]} ; done >> $base-lig.top

fi


## BOOKKEEPING ##

# Bookkeeping is always done, also if the step is not executed 
# In this case only if we actually had ligands

if [[ ${#LIGANDS[@]} -gt 0  ]] 
then    

    if [[ -e $base-lig.gro ]]
    then
	LATOMS=$( $SED  -n '2{p;q;}' $base-lig.gro)
	Solute=(1 $LATOMS)
	[[ -e $GRO ]] && NATOMS=$(( $( $SED  -n '2{p;q;}' $base.gro) + 1 )) || NATOMS=1
	Ligand=($NATOMS $LATOMS)
    fi

    # Set the correct structure/topology file as master structure/topology
    GRO=$base-lig.gro
    TOP=$base-lig.top
fi


# End of step
[[ $STOP ==   $NOW     ]] && exit_clean
[[ $STEP == $((NOW++)) ]] && : $((STEP++))


#--------------------------------------------------------------------
#ECHO "#---STEP 1C: (GUESS... :))"
#--------------------------------------------------------------------


#--------------------------------------------------------------------
ECHO "#---STEP 2: SET PERIODIC BOUNDARY CONDITIONS"
#--------------------------------------------------------------------


# Output for this section:
OUTPUT=($base-pbc.gro)


# Log file
LOG=02-PBC.log


# Delete existing output if we force this step
[[ $STEP == $NOW ]] && $FORCE && rm ${OUTPUT[@]}


# If there is no structure file at this point, build a 
# rhombic dodecahedron with diameter $PBCDIST
if [[ $STEP == $NOW && ! -f $GRO ]]
then
    echo -e "Solvent box\n    0" > $base-pbc.gro    
    python -c "print \"\".join([\"%10.5f\"%($PBCDIST*i) for i in [1,1,.7071068,0,0,0,0,.5,.5]])" >> $base-pbc.gro

    # Skip the rest of this step
    # Also skip the following step (little sense in EM in vacuum if there is nothing in the vacuum)
    : $((STEP+=2))
fi


## I. Build command

## 1. Select the program
if $NDLP
then
    PBC="$GMXBIN/taw_squeeze -f $GRO -s $GRO -o $base-pbc.gro -d $PBCDIST -c"
    tag=squeeze
else
    PBCDIST=$(python -c "print 0.5*$PBCDIST")
    PBC="$GMXBIN/editconf -f $GRO -o $base-pbc.gro -bt dodecahedron -d $PBCDIST -c"
    tag=editconf
fi

## 2. Add program options specified on command line
PBC="$PBC $(program_options $tag)"

## 3. Process
if [[ $STEP == $NOW && -n $EXEC ]]
then
    # Not running, but showing what would have been run
    echo "Skipping: $PBC"   
elif [[ $STEP == $NOW ]] && $(all_exist ${OUTPUT[@]})
then
    echo "Output found. Skipping setting up PBC."
elif [[ $STEP == $NOW ]]
then
    # touch aminoacids.dat
    echo `date`: $PBC | tee $LOG
    echo 0 0 0 | $PBC >>$LOG 2>&1

    # Check the box. The minimum vector length should be 3
    # We only check the first value, which is the length of
    # the first vector. For a rhombic dodecahedron it is the 
    # length of all vectors. For an NDLP unit cell it gives
    # the length of the longest vector. If that is less than
    # 3, the cell is obviously too small. In both cases, the 
    # cell is replaced by a rhombic dodecahedron with length 3.
    box=($(tail -1 $base-pbc.gro))
    if [[ ${box%%.*} -lt 3 ]]
    then
	cat << __WARNING__

WARNING:

The box set up according to the method ($tag) 
and the distance criterion ($PBCDIST) is too small:

u: ${box[0]} ${box[3]} ${box[4]}
v: ${box[1]} ${box[5]} ${box[6]}
w: ${box[2]} ${box[7]} ${box[8]}

Replacing box with a rhombic dodecahedron of radius 3.

__WARNING__

	box='   3.00000   3.00000   2.12132   0.00000   0.00000   0.00000   0.00000   1.50000   1.50000'
	$SED -i -e "\$c $box" $base-pbc.gro
	
    fi

    # rm aminoacids.dat
fi

## BOOKKEEPING ##


# bookkeeping is always done, also if the step is not executed 

GRO=$base-pbc.gro


# End of step
[[ $STOP ==   $NOW     ]] && exit_clean
[[ $STEP == $((NOW++)) ]] && : $((STEP++))


#--------------------------------------------------------------------
ECHO "#---STEP 3: RUN EM IN VACUUM"
#--------------------------------------------------------------------

PROGOPTS+=("--grompp=-maxwarn 1")

trash $base-EMv.{tpr,edr,log,trr} em-vac-out.mdp

MDP=em-vac.mdp
OPT=(em)
OUT=$base-EMv.gro
LOG=03-EMv.log

# Command for running MD
MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -np 1 -l $LOG -force $FORCE" # -onepr"

if [[ $STEP == $NOW ]]
then

    # Set name of GRO file to output of EM
    GRO=$OUT

    # Generate mdp file
    mdp_options ${OPT[@]} > $MDP
    $SED -i 's/_/-/g' $MDP

    # Execute command
    $EXEC $MD && : $((STEP++))
fi

# Check for exit
[[ $STOP == $((NOW++)) ]] && exit_clean


#--------------------------------------------------------------------
ECHO "#---STEP 4: SOLVATION AND ADDING IONS"
#--------------------------------------------------------------------


OUTPUT=($base-sol.gro $base-sol.top $base-sol.ndx)


# If there is no topology file yet, we have to set one up
[[ -z $TOP ]] && TOP=$base.top && cat << __TOP__ > $base.top
#include "$ForceField.ff/forcefield.itp

[ system ]
Box of solvent, maybe with ions

[ molecules ]
__TOP__


# If we execute this step and we force regeneration of files
# then delete any output files that may be present
[[ $STEP == $NOW ]] && $FORCE && rm ${OUTPUT[@]}


# Check output
if [[ $STEP == $NOW && $(all_exist ${OUTPUT[@]}) ]]
then
    echo Found output... Skipping addition of solvent\(s\).
    : $((STEP++))
fi


if [[ $STEP == $NOW ]]
then

    LOG=04-SOLVATION.log

    # Mark redundant files generated in this step
    trash $base-sol-b4ions.{gro,top,tpr} sol-b4ions.ndx genion.log genion_node0.log b4ions.pqr empty.mdp defaults.mdp


    ## 1. Solvation

    # a. Basic stuff
    GENBOX="$GMXBIN/genbox -cp $GRO -cs -o $base-sol-b4ions.gro"

    # b. Add program specific options from command line
    GENBOX="$GENBOX $(program_options genbox)"

    # c. Make noise
    echo `date`: $GENBOX | tee $LOG
    
    # d. Execute
    $EXEC $GENBOX >>$LOG 2>&1

    # e. Extract number of atoms before adding solvent and amount of solvent added from log
    SED_SOL="/^Generated solvent/{s/^.*in \(.*\) residues/\1/;p}"
    SED_ATOMS="/^Containing/{s/^Containing \(.*\) atoms.*/\1/;p}"
    NATOMS=(` $SED -n -e "{ $SED_SOL }" -e "{ $SED_ATOMS }" $LOG`)
    NSOL=${NATOMS[1]}

    # f. Update topology: add the number of solvent molecules added
    cp $TOP $base-sol-b4ions.top
    printf "SOL %17d ; B4IONS\n" $NSOL >> $base-sol-b4ions.top

    # g. Add solvent model include file if it is not present yet
    #    First check if there is a moleculetype named 'SOL'
    #    This is a bit awkward and may give wrong results if we use 
    #    solvent other than water, but it is necessary to prevent 
    #    redefining the SOL moleculetype in certain (eTox) cases.
    if [[ ! $( $SED -n '/^ *\[ *moleculetype *\]/{:a;n;/^ *;/ba;p}' $TOP) =~ SOL ]] 
    then
	# check if a file is #included with the solvent model
	grep -q '#include.*'$SolModel'.itp' $TOP || $SED -i "/^\[ *system *\]/i #include \"$SolModel.itp\"\n" $base-sol-b4ions.top
    fi

    # h. Make some more noise
    echo Solvent added: $NSOL molecules
	

    ## 2. Adding ions

    #
    # NOTES
    # 
    # One could argue that the following is taking bash over the top. And that is true.
    # It would be easier and neater just using python. In addition, it could even be left
    # to 'genion', which has options for neutralization and specification of the 
    # concentration. 
    # Yet there are several reasons for doing this here. First of all, the reason for 
    # doing it ourselves is that genion uses the box volume to calculate the number of
    # ions to add, given the volume. This assumes that the solvent in the box has 
    # equilibrium density already, and that the space occupied by solute counts as space
    # to consider for ions. The latter neglects the difference between macroscopic and 
    # microscopic solutions of macromolecules and the fact that such macromolecules are 
    # solvated in an isotonic solution, rather than brought to isotonicity afterwards,
    # based on the volume of the macromolecule solution. 
    # Another reason for doing it here is ... because we can :) Yes, it is showing off
    # to some extent, but it also demonstrates some features of bash, in particular 
    # related to integer math, which may come in handy.
    # Admittedly, this is not the most efficient way to handle this. But compared to the
    # simulation bits, the overhead is limited.
    #
    # On to adding ions...
    #


    # a. First extract net charge
    #    Combine the topology and structure, yielding a full listing of atoms and charges
    touch empty.mdp
    tag="sol-b4ions"
    GROMPP="$GMXBIN/grompp -v -f empty.mdp -c $base-$tag.gro -p $base-$tag.top -o $base-$tag.tpr -po defaults.mdp $(program_options grompp)"


    # b. Tell what is happening
    echo `date`: $GROMPP | tee -a $LOG


    # c. Execute
    $NOEXEC $GROMPP >>$LOG 2>&1


    # d. Get the charge of the system
    #    For LIE calculations only calculate the charge excluding the ligand
    #    At this point, that corresponds to the 'ligand environment' group
    #    since we have not added the solvent to it.
    #    So first we create an index group, if needed.
    NDX=
    if $LIE
    then
	echo Excluding ligand from charge calculation
	# Of course, this only makes sense if we have something other than ligand
	if [[ -n $Ligenv ]]
	then
	    printf "%5d %5d %5d %5d %5d\n" $(SEQ ${Ligenv[@]}) | $SED 's/ 0//g;1i[ check ]' > charge.ndx
	    NDX="-n charge.ndx"
	    trash charge.ndx
	fi
    fi
    #    Then we convert the run input file to a .pqr file, from which we parse the charges 
    NCHARGE=0
    if [[ -z $NDX || -n $Ligenv ]]
    then
	$GMXBIN/editconf -f $base-sol-b4ions.tpr -mead b4ions.pqr $NDX >/dev/null 2>&1	
	NCHARGE=$(awk '/^ATOM/{S+=substr($0,62,6)}END{printf "%.0f", S}' b4ions.pqr)
    fi
    echo Net charge of system: $NCHARGE


    # e. Check if we should neutralize the system ... and whether we do
    [[ -n $CHARGE ]] && echo Setting charge to $CHARGE, while system charge is $NCHARGE && NCHARGE=$CHARGE
    [[ $NCHARGE != 0 && ${Salinity:0:1} == - ]] && NCHARGE=0 && echo Not adding counterions, despite charge.


    # f. Calculate NPOS and NNEG given the charge and salinity, correcting for water removed

    #    i.    Salt: aX^+m, bY^n
    #          Infer stoichiometry from names - Check if salt name starts with a number
    [[ ${Salt[0]} =~ ^[0-9] ]] && a=${Salt[0]%%[^0-9]*} || a=1
    [[ ${Salt[1]} =~ ^[0-9] ]] && b=${Salt[1]%%[^0-9]*} || b=1

    #    ii.   Set names for ions - Strip the number in front (if any)
    PNAM=${Salt[0]#$a}
    NNAM=${Salt[1]#$b}    
	
    #    iii.  Now if Q is the number of ions to be added, and S is the number of solvent molecules, then
    #              Q = PS / 55.4(1+P)
    #          if the solvent is water and has a molarity of 55.4, and P = C(a+b) is the number of
    #          ions per liter, with C being the concentration of the salt.
    #          We cheat by calling python for floating point arithmetics.
    #          Yes, we could have used bc...
    Q=$(python -c "print int(0.5+$Salinity*($a+$b)*$NSOL/(55.4+$Salinity*($a+$b)))")

    #    iv.   Let U and V denote the number of positive and negative ions, respectively, then for
    #          a system with a net charge equal to Z we have
    #             Z = Um + Vn           (u and v integer)
    #             Q = U  + V
    #             U = (Qn - Z)/(n - m)
    #             V = (Z - Qn)/(m - n)
    m=${SaltCharge[0]}
    n=${SaltCharge[1]}
    U=$(python -c "print int(0.5+( $Q*$n+$NCHARGE)/($n-$m))")
    V=$(python -c "print int(0.5+(-$Q*$m-$NCHARGE)/($n-$m))")

    #    v.    Now U and V may still be slightly off, so we correct iteratively
    #          If the net charge is odd and the difference between charges is
    #          even, then it will never converge...
    prev=(999 999)
    i=0
    while [[ $((-U*m-V*n)) != $NCHARGE ]] 
    do
	# If the charge is too low, increase the number of positives
	[[ $((-U*m-V*n)) -lt $NCHARGE ]] && : $((U--))
	# If the number is still too low, decrease the number of negatives
	[[ $((-U*m-V*n)) -lt $NCHARGE ]] && : $((V++))
	# If the number is too high, increase the number of negatives
	[[ $((-U*m-V*n)) -gt $NCHARGE ]] && : $((V--))
	# If the number is still too high, decrease the number of positives
	[[ $((-U*m-V*n)) -gt $NCHARGE ]] && : $((U++))
	# Store the net charge with this configuration
	prev[${#prev[@]}]=$((-U*m-V*n))
	# Check if we are in an endless loop
	echo $i $U $V $((-U*m-V*n)) ${prev[@]}
	[[ $((-U*m-V*n)) == ${prev[$((i++))]} ]] && echo Breaking out of endless loop && break
	[[ $i -gt 100 ]] && echo 100 iterations and counting. This is hopeless. Bailing out. Check your salt. && exit_error 41 
    done

    #    vi.   Check if one of the two is negative, and correct if so
    [[ $U -lt 0 ]] && : $((V-=U)) && U=0
    [[ $V -lt 0 ]] && : $((U-=V)) && V=0


    #NCL=$(python -c "print max(min(0,$NCHARGE),int(0.5+0.5*($Salinity*$NSOL/(27.7+$Salinity)+$NCHARGE)))")
    #NNA=$((NCL-NCHARGE))
    echo "Replacing $(( U + V )) solvent molecules with $U $PNAM ($m) and $V $NNAM ($n) ions."

    # - Make an index file for the solvent added for genion
    echo "[ SOL ]" > sol-b4ions.ndx

    # Make a listing of the solvent added with respect to the output from EM
    N1=$(( $( $SED  -n '2{p;q;}' $GRO) + 1 ))
    N2=$( $SED  -n '2{p;q;}' $base-sol-b4ions.gro)
    printf "%5d %5d %5d %5d %5d\n" $(SEQ $N1 $N2) | $SED 's/ 0//g;1i[ SOL ]' > sol.ndx
    
    # Only call genion if ions should be added
    if [[ $((U + V)) -gt 0 ]]
    then
        # - Then call genion
        GENION="$GMXBIN/genion -s $base-sol-b4ions.tpr -o $base-sol.gro -n sol.ndx"
        GENION="$GENION -pname $PNAM -nname $NNAM -np $U -nn $V -pq $m -nq $n -rmin 0.5"

        echo `date`: $GENION | tee -a $LOG

        $GENION >>$LOG 2>&1
    
        # - And finally, update the topology
	#   Do check if 'ions.itp' is included
	grep -q '#include.*ions.itp' $base-sol-b4ions.top && IONSITP= || IONSITP='-e /^\[ *system *\]/i#include "ions.itp"\n'
        $SED "$IONSITP" -e /B4IONS/d $base-sol-b4ions.top > $base-sol.top
        printf "SOL %17d\n$PNAM %17d\n$NNAM %17d" $(( NSOL - U - V )) $U $V >> $base-sol.top	
    else
        $SED s/B4IONS// $base-sol-b4ions.top > $base-sol.top
        cp $base-sol-b4ions.gro $base-sol.gro
    fi
	
elif [[ $STEP == $STOP ]]
then
    $(all_exist ${OUTPUT[@]}) && echo -e "Output files present...\nSkipping: $GENBOX"
    $EXEC && echo -e "Not executing: $GENBOX"
fi


## BOOKKEEPING ##

# bookkeeping is always done, also if the step is not executed 

# If we need the ligand interaction energy, set the energy groups to
# ligand and environment, otherwise set to solute and solvent
$LIE && EnergyGroups=(Ligand Ligenv) || EnergyGroups=(Solute Solvent)

# The temperature coupling groups are solute (including ligands)
# and solvent (including ions)
CoupleGroups=(Solute Solvent)

if [[ -e $base-sol.gro ]]
then
    # Now see how much solvent was added in total and list in the right group
    # Also add to the ligand environment
    N2=$( $SED  -n '2{p;q;}' $base-sol.gro)
    Solvent[${#Solvent[@]}]=$N1
    Solvent[${#Solvent[@]}]=$N2
    Ligenv[${#Ligenv[@]}]=$N1
    Ligenv[${#Ligenv[@]}]=$N2


    if [[ ! -e $base-sol.ndx ]]
    then
        ## WRITE MASTER INDEX FILE ##
    
        # Here the whole system has been built. Time to make an index file with all the definitions needed

        # First a basic one
	echo q | $GMXBIN/make_ndx -f $base-sol.gro -o $base-sol.ndx >/dev/null 2>&1

        # Add the Solute and Solvent (and Membrane?) groups
	fmt="%5d %5d %5d %5d %5d %5d %5d %5d %5d %5d"    
	echo "[ Solute ]" >> $base-sol.ndx
	for ((i=0; i<${#Solute[@]}; ))
	do
	    A=${Solute[$((i++))]}
	    B=${Solute[$((i++))]}
	    printf "$fmt\n" `SEQ $A $B` | $SED 's/ 0//g' >> $base-sol.ndx
	done
	echo "[ Membrane ]" >> $base-sol.ndx
	for ((i=0; i<${#Membrane[@]}; ))
	do
	    A=${Membrane[$((i++))]}
	    B=${Membrane[$((i++))]}
	    printf "$fmt\n" `SEQ $A $B` | $SED 's/ 0//g' >> $base-sol.ndx
	done
	echo "[ Solvent ]" >> $base-sol.ndx
	for ((i=0; i<${#Solvent[@]}; ))
	do
	    A=${Solvent[$((i++))]}
	    B=${Solvent[$((i++))]}
	    printf "$fmt\n" `SEQ $A $B` | $SED 's/ 0//g' >> $base-sol.ndx
	done
        # Finally add the ligand and ligenv groups if any ligands were added
	if [[ ${#LIGANDS[@]} -gt 0 ]]
	then
	    echo "[ Ligand ]" >> $base-sol.ndx
	    for ((i=0; i<${#Ligand[@]}; ))
	    do
		A=${Ligand[$((i++))]}
		B=${Ligand[$((i++))]}
		printf "$fmt\n" `SEQ $A $B` | $SED 's/ 0//g' >> $base-sol.ndx
	    done	
	    echo "[ Ligenv ]" >> $base-sol.ndx
	    for ((i=0; i<${#Ligenv[@]}; ))
	    do
		A=${Ligenv[$((i++))]}
		B=${Ligenv[$((i++))]}
		printf "$fmt\n" `SEQ $A $B` | $SED 's/ 0//g' >> $base-sol.ndx
	    done	
	fi
    fi
fi

[[ $STOP ==   $NOW     ]] && exit_clean
[[ $STEP == $((NOW++)) ]] && : $((STEP++))

#--------------------------------------------------------------------
ECHO "#---STEP 5: ENERGY MINIMIZATION IN SOLVENT (NVT)"
#--------------------------------------------------------------------

trash $base-EMs.{tpr,log,trr} em-sol-out.mdp

# Turn on PBC for EM
__mdp_em__pbc=xyz
#__mdp_em__define=-DPOSRES
__mdp_em__energygrps=$( $SED 's/ /,/g' <<< ${EnergyGroups[@]})

NDX=$base-sol.ndx
MDP=em-sol.mdp
OPT=(em)
TOP=$base-sol.top
GRO=$base-sol.gro
OUT=$base-EMs.gro
LOG=05-EMs.log

#MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT  -n $NDX -np $NP -l $LOG -force $FORCE"
MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT  -n $NDX -l $LOG -force $FORCE"
#ANALENE="$GMXBIN/gmxdump -e $base-EMs.edr"
#echo $ANALENE

[[ $STEP ==   $NOW     ]] && mdp_options ${OPT[@]} > $MDP && $SED -i 's/_/-/g' $MDP
[[ $STEP ==   $NOW     ]] && $EXEC $MD &&: $((STEP++)) && archive
[[ $STOP == $((NOW++)) ]] && exit_clean


#----------------------------------------------------------------------------------
ECHO "#---STEP 6: POSITION RESTRAINT MD, NVT -- CYCLE THROUGH PRFC AND TEMP/TAU_T"
#----------------------------------------------------------------------------------

PROGOPTS+=("--grompp=-r $base-EMs.gro")

if [[ $Electrostatics == PME ]]
then
    # Do not use a force field tag; just use mdp defaults
    ForceFieldMDP=
else
    ForceFieldMDP=$ForceFieldFamily
fi

echo ${CoupleGroups[@]}
__mdp_md__tc_grps=$(    $SED 's/ /,/g' <<< ${CoupleGroups[@]})
__mdp_md__energygrps=$( $SED 's/ /,/g' <<< ${EnergyGroups[@]})

# Only print stuff if we actually execute this step

if [[ $STEP == $NOW ]]
then
    echo "Equilibration (NVT/PR):"
    echo Temperatures: ${Temperature[@]}
    echo Coupling times: ${Tau_T[@]}
    echo Position restraint Fcs: ${PosreFC[@]}
fi

NDX=$base-sol.ndx
TOP=$base-sol.top
GRO=$base-EMs.gro
LOG=06-PR-NVT.log

# To avoid too much overhead, identify files with a position restraint tag
posre=($(grep -l POSCOS *top *itp))

# Counters
i=0
j=0
k=0
# Numbers
I=$((${#Temperature[@]}-1))
J=$((${#Tau_T[@]}-1))
K=$((${#PosreFC[@]}-1))
while :
do

    # Set the temperature and the position restraint force for this cycle
    T=${Temperature[$i]}
    tau=${Tau_T[$j]}
    F=${PosreFC[$k]}

    # Specify temperature for each group (Solute/Solvent/Membrane)
    # Note that this (re)sets the master temperature control
    __mdp_md__ref_t=$( $SED  's/ /,/g' <<< $(for i in ${CoupleGroups[@]}; do echo $T;   done))
    __mdp_md__tau_t=$( $SED  's/ /,/g' <<< $(for i in ${CoupleGroups[@]}; do echo $tau; done))

    if [[ $STEP == $NOW ]]
    then
    # Modify position restraint definitions
        __mdp_equil__nsteps=$(python -c "print int(1000*$Equi_time/$__mdp_equil__dt + 0.5 )")
        __mdp_equil__nstlog=$(python -c "print int(2/$__mdp_equil__dt)" )
        __mdp_equil__nstvout=$(python -c "print int(2/$__mdp_equil__dt)" )
        __mdp_equil__nstenergy=$(python -c "print int(2/$__mdp_equil__dt)" )
        __mdp_equil__nstxout=$(python -c "print int(2/$__mdp_equil__dt)" )
        pos2=$(python -c "print int($F/2)" )
        pos3=$(python -c "print int($F/5)" )
        pos4=$(python -c "print int($F/10)" )
        pos5=$(python -c "print int($F/10)" )
        if [ ${#posre[@]} -gt 0 ]
            then
            $SED -i "s/^\( *#define \+1POSCOS\).*\$/\1 $F/" ${posre[@]}
            $SED -i "s/^\( *#define \+2POSCOS\).*\$/\1 $pos2/" ${posre[@]}
            $SED -i "s/^\( *#define \+3POSCOS\).*\$/\1 $pos3/" ${posre[@]}
            $SED -i "s/^\( *#define \+4POSCOS\).*\$/\1 $pos4/" ${posre[@]}
            $SED -i "s/^\( *#define \+5POSCOS\).*\$/\1 $pos5/" ${posre[@]}
        fi
     #Make some noise
	echo NVT Equilibration at $T Kelvin \(tau_t=$tau\) with Position restraint force $F
    fi

    # Set the file names and such for this cycle
    MDP=pr-$F-nvt-$T-$tau.mdp
    OPT=(md $ForceFieldMDP equil usr)
    OUT=$base-PR-$F-NVT-$T-$tau.gro

    # Build the command
    MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -n $NDX -l $LOG -force $FORCE"
    # Execute
    [[ $STEP ==   $NOW     ]] && mdp_options ${OPT[@]} > $MDP && $SED -i 's/_/-/g' $MDP
    [[ $STEP ==   $NOW     ]] && $EXEC $MD 

    # Set current structure to last output structure
    GRO=$OUT

    # Disable generation of velocities after first cycle
    __mdp_equil__genvel=no

    # Break the loop if all values are at maximum
    if [[ $i == $I && $j == $J && $k == $K ]]
    then
	break
    fi

    # Increment the counters if there are more entries for it
    # A note for whoever is reading this: ':' is a bash command
    # which is just 'true', and can be used conveniently for 
    # doing in-place math operations using $(( )).
    [[ $i -lt $I ]] && : $(( i++ ))
    [[ $j -lt $J ]] && : $(( j++ ))
    [[ $k -lt $K ]] && : $(( k++ ))
  
done


# Store intermediate results if we just finished a step
[[ $STEP ==   $NOW     ]] && : $((STEP++)) && archive

# Exit if this step is the stop step
[[ $STOP == $((NOW++)) ]] && exit_clean


#----------------------------------------------------------------------------
ECHO "#---STEP 7: UNRESTRAINED MD 20 ps NPT -- CYCLE THROUGH PRESSURE/TAU_P"
#----------------------------------------------------------------------------

# Turning on the pressure
__mdp_md__pcoupl=Berendsen

Equi_time=0.02

if $VirtualSites; then
  __mdp_equil__dt=0.004
  __mdp_equil__lincsorder=4
  __mdp_equil_nstlist=2
fi

__mdp_equil__nsteps=$(python -c "print int(1000*$Equi_time/$__mdp_equil__dt + 0.5 )")        

# Relieve position restraints
__mdp_equil__define=


if [[ $STEP == $NOW ]]
then
    echo "Equilibration (NpT):"
    echo Pressures: ${Pressure[@]}
    echo Coupling times: ${Tau_P[@]}
fi

TOP=$base-sol.top
GRO=$OUT 
LOG=07-NPT.log

# Counters
i=0
j=0
# Numbers
I=$((${#Pressure[@]}-1))
J=$((${#Tau_P[@]}-1))
while :
do
    # Set the pressure and coupling time for this cycle
    P=${Pressure[$i]}
    tau=${Tau_P[$j]}


    # Specify pressure
    # Note that this (re)sets the master pressure control
    __mdp_md__ref_p=$P
    __mdp_md__tau_p=$tau


    # Make some noise if we are actually executing this step
    [[ $STEP == $NOW ]] && echo NpT Equilibration at $P bar \(tau_p=$tau\)


    # Set the file names and such for this cycle
    MDP=npt-$P-$tau.mdp
    OPT=(md $ForceFieldMDP equil $RotationalConstraints usr)
    OUT=$base-NPT-$P-$tau.gro


    # Build the command
#    MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -n $NDX -np $NP -l $LOG -force $FORCE"
    MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -n $NDX -l $LOG -force $FORCE"

    # Execute
    [[ $STEP ==   $NOW     ]] && mdp_options ${OPT[@]} > $MDP && $SED -i 's/_/-/g' $MDP
    [[ $STEP ==   $NOW     ]] && $EXEC $MD 

    # Set current structure to last output structure
    GRO=$OUT

    # Break the loop if all values are at maximum
    if [[ $i == $I && $j == $J ]]
    then
	break
    fi

    # Increment the counters if there are more entries for it
    # A note for whoever is reading this: ':' is a bash command
    # which is just 'true', and can be used conveniently for 
    # doing in-place math operations using $(( )).
    [[ $i -lt $I ]] && : $(( i++ ))
    [[ $j -lt $J ]] && : $(( j++ ))
  
done


# Store intermediate results if we just finished a step
[[ $STEP ==   $NOW     ]] && : $((STEP++)) && archive

# Exit if this step is the stop step
[[ $STOP == $((NOW++)) ]] && exit_clean


#--------------------------------------------------------------------
ECHO "#---STEP 8: SHORT RUN UNDER PRODUCTION CONDITIONS"
#--------------------------------------------------------------------

  # skip this step
echo $STEP
[[ $STEP ==   $NOW     ]] && : $((STEP++))
echo $STEP

[[ $STOP == $((NOW++)) ]] && exit_clean


#--------------------------------------------------------------------
ECHO "#---STEP 9: PRODUCTION RUN"
#--------------------------------------------------------------------

MDP=md-prod.mdp
OPT=(md $ForceFieldMDP $RotationalConstraints usr)
TOP=$base-sol.top
GRO=$OUT
OUT=$base-MD.gro
LOG=09-MD.log

#MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -n $NDX -np $NP -l $LOG -force $FORCE -split"
MD="MDRUNNER -f $MDP -c $GRO -p $TOP -o $OUT -n $NDX -l $LOG -force $FORCE"


[[ $STEP ==   $NOW     ]] && mdp_options ${OPT[@]} > $MDP &&     $SED -i 's/_/-/g' $MDP
[[ $STEP ==   $NOW     ]] && $EXEC $MD && DONE=$?  && : $((STEP++)) && archive
#[[ $STOP == $((NOW++)) ]] && exit_clean

echo "Exit status: $DONE"
# Only here, the clean exit depends on the exit code of the MD run
# The function exits with 1 if the run was not finished yet.
[[ $DONE == 0 ]] && exit_clean

#--------------------------------------------------------------------
#---THE END
#--------------------------------------------------------------------
