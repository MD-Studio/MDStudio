#!/usr/bin/env bash

# LIEStudio installer script
# version 1.0
# Author: Marc van Dijk, VU University Amsterdam
# August 2016

# Get root directory of script
pushd `dirname $0` > /dev/null
ROOTDIR=`pwd -P`
popd > /dev/null

# CLI variables
SETUP=0
UPDATE=0
TEST=0
COMPILE_DOCS=0
VERBOSITY='debug'
PYTHON='python3.4'
VENVTOOL=
FORCE=0

# Internal variables
_PYTHON_PATH=
_PYV=
_PY_SUPPORTED=( 2\.7\* 3\.4\* 3\.5\* )
_PY_VENV=
_PY_VENV_ACTIVE=0
_VENVPATH=${ROOTDIR}'/lie_venv'

USAGE="""LIEStudio setup script

This script installes or updates the LIEStudio 
software on your system.

Main options:
-s|--setup:         Install LIE Software package by executing the subroutines (below)
                    with default values.
-u|--update:        Update LIE Software package by executing the subroutines (below)
                    with default values.     
            
Subroutines:
-f|--force:         Force reinstall or update.
                    Default: $FORCE
-t|--test:          Run Python unittests.
                    Default: $TEST
-d|--documentation: Compile HTML documentation for the software and API.
                    documentation of the Python modules.
                    Default = $COMPILE_DOCS

Installation/update variables:
-p|--python:        Python version to use.
                    Default = $PYTHON
-e|--venv:          Python virtual environment tools to use.
                    Currently build-in venv module of Python 3.4> or Python 2.x virtualenv
-v|--verbosity:     verbosity level.
                    Default = $VERBOSITY
                    
-h|--help:          This help message
"""

# Command line argument handling
for i in "$@"; do
  case $i in
    -h|--help)
    echo "$USAGE"
    exit 0
    shift # past argument with no value
    ;;
    -f|--force)
    FORCE=1
    shift # past argument with no value
    ;;
    -s|--setup)
    SETUP=1
    shift # past argument with no value
    ;;
    -u|--update)
    UPDATE=1
    shift # past argument with no value
    ;;
    -t|--test)
    TEST=1
    shift # past argument with no value
    ;;
    -d|--documentation)
    COMPILE_DOCS=1
    shift # past argument with no value
    ;;
    -p=*|--python=*)
    PYTHON="${i#*=}"
    shift # past argument=value
    ;;
    -e=*|--venv=*)
    VENVTOOL="${i#*=}"
    shift # past argument=value
    ;;
    -v=*|--verbosity=*)
    VERBOSITY="${i#*=}"
    shift # past argument=value
    ;;
    *)
    echo "$USAGE"
    exit 0 # unknown option
    ;;
  esac
done


# Check Python version
# - Check for prefered python version, default $PYTHON
# - Check CLI defined python path or name
# - Check Python version in users path
function _resolve_python_version () {
  
  # Check if $PYTHON is a path to Python exec.
  # If not, check if we can find using which
  if [[ -f $PYTHON ]]; then
    _PYTHON_PATH=$PYTHON
  else
    _PYTHON_PATH=$( which ${PYTHON##*/} )
  fi
  
  # Unable to find $PYTHON. Check python version in 
  # users path against supported versions.
  if [[ -z $_PYTHON_PATH ]]; then
    _PYV=$( python --version 2>&1 | awk '{print $2}')
    
    if [[ -z $_PYV ]]; then
      echo "ERROR: Unable to detect any 'python' executable in your path"
      exit 1
    fi
    
    for pyv in "${_PY_SUPPORTED[@]}"; do
      if [[ $_PYV == $pyv ]]; then
        _PYTHON_PATH=$( which python )
        echo "INFO: Using supported python version $_PYV in path"
        break
      fi
    done
    
    if [[ -z $_PYTHON_PATH ]]; then
      echo "ERROR: LIEStudio supports python version "${_PY_SUPPORTED[@]}". Found: $_PYV"
      echo "ERROR: If you have one of the supported Python versions installed, supply the path using the -p/--python argument"
      exit 1
    fi
  
  else
    _PYV=$( $_PYTHON_PATH --version 2>&1 | awk '{print $2}')
    echo "INFO: Using Python version $_PYV at $_PYTHON_PATH"     
  fi
}

# Check Python virtual environment options
# - If python version 3, use standard lib venv module
# - If python version 2.x then check if virtualenv is installed
function _resolve_python_venv () {
  
  # Python 3.4 or larger, use buildin venv module  
  if [[ $_PYV == 3\.* ]]; then
    echo "INFO: Using Python version $_PYV Virtual environment module (venv) part of standard library"
    _PY_VENV="$_PYTHON_PATH -m venv"
  
  # Python 2.x look for virtualenv tool
  else
    #IFS='.' read -ra _pyv_split <<< $_PYV
    
    # If user provided path to virtualenv tool (-e/-venv), check
    if [[ -f $VENVTOOL ]]; then
      _PY_VENV="$VENVTOOL -p $_PYTHON_PATH"
    
    else   
      # Look for virtualenv tool that may be named differently
      local _virtualenv
      local _pyv_venv_options=( "virtualenv" "virtualenv-${_PYV%.*}" )
      for pyv_venv in "${_pyv_venv_options[@]}"; do
        _virtualenv=$( which $pyv_venv )
        if [[ ! -z $_virtualenv ]]; then
          break
        fi
      done
    
      if [[ -z $_virtualenv ]]; then
        echo "ERROR: For Python version $_PYV the 'virtualenv' tool is required for installation of LIEstudio dependencies"
        echo "ERROR: It could not be found looking for: "${_pyv_venv_options[@]}" $VENVTOOL"
        echo "ERROR: If you have virtualenv installed, supply the path using the -e/--venv argument or"
        echo "ERROR: Install using 'pip install virtualenv' or similar"
        exit 1
      fi
    
      _PY_VENV="$_virtualenv -p $_PYTHON_PATH"
    fi
  fi
  
  echo "INFO: Setup Python virtual environment using $_PY_VENV"
}

# Check the directory structure
function _check_dir_structure () {
  
  for path in '/data/logs' '/docs'; do
    if [ ! -d ${ROOTDIR}$path ]; then
      echo "INFO: Create directory ${ROOTDIR}$path"
      mkdir ${ROOTDIR}$path
    fi
  done
}

# Setup the Python virtual environment
function _setup_venv () {
  
  # Create or upgrade the Python virtual environment
  if [ -d $_VENVPATH ]; then
    
    # Remove and reinstall venv
    if [[ $FORCE -eq 1 ]]; then
      echo "INFO: Reinstall Python virtual environment at $_VENVPATH"
      \rm -rf $_VENVPATH
      $_PY_VENV $_VENVPATH
    else
      echo "INFO: Virtual environment present, not reinstalling"
    fi
    
  else
    echo "INFO: Create Python virtual environment at: $_VENVPATH"
    $_PY_VENV $_VENVPATH
  fi
  
  # Set execute permissions for scripts in /bin
  echo "INFO: grant executable permissions to scripts in ${_VENVPATH}/bin"
  for file in $( ls ${_VENVPATH}/bin/* ); do
    chmod +x $file
  done
  
  # Activate venv
  _activate_py_venv
  
  # Check if pip is in virtual environment
  PIPPATH=$( which pip )
  if [[ ! "$PIPPATH" == "${_VENVPATH}/bin/pip" ]]; then
    echo "ERROR: unable to activate Python virtual environment"
    exit 1
  fi
  
  # Update virtual environment
  if [[ $UPDATE -eq 1 ]]; then
    echo "INFO: Update Python virtual environment at $_VENVPATH"
    echo "TODO: Check Git for newer LIEStudio version and associated python_default_requirements.txt"
  else
    # Download and install requirements in python_default_requirements.txt
    pip install -r ${ROOTDIR}/data/python_default_requirements.txt
  fi
  
  # Install all LIEStudio component packages and their dependencies using pip
  local _force_reinstall=''
  [[  $UPDATE -eq 1 ]] && _force_reinstall='--upgrade'
  for package in $( ls -d ${ROOTDIR}/components/*/ ); do
    if [[ -e ${package}setup.py ]]; then
      echo "INFO: Install LIEStudio Python component ${package}"
      pip install $_force_reinstall $package
    fi
  done
}

# Compile LIEStudio and API documentation as HTML using Sphinx
function _compile_python_sphinx_docs () {
  
  # Build API documentation for components
  # - First remove previous components.*.rst files
  echo "INFO: Build API documentation for LIEStudio Python modules in /components"
  
  # Make a modules.rst file
  echo "Components" >> ${ROOTDIR}/docs/tmp_modules.rst
  echo "==========" >> ${ROOTDIR}/docs/tmp_modules.rst
  echo "" >> ${ROOTDIR}/docs/tmp_modules.rst
  echo ".. toctree::" >> ${ROOTDIR}/docs/tmp_modules.rst
  echo "   :maxdepth: 4" >> ${ROOTDIR}/docs/tmp_modules.rst
  echo "" >> ${ROOTDIR}/docs/tmp_modules.rst
  
  for module in $( ls -d ${ROOTDIR}/components/lie_*/lie_* ); do
    module_name=${module##*/}
    rm -rf ${ROOTDIR}/docs/${module_name}.rst
    
    sphinx-apidoc --module-first --private --force -o ${ROOTDIR}/docs/ ${module}/
    
    echo "   ${module_name}" >> ${ROOTDIR}/docs/tmp_modules.rst
  done
  
  mv ${ROOTDIR}/docs/tmp_modules.rst ${ROOTDIR}/docs/modules.rst
  
  # Build documentation
  echo "INFO: Compile LIEStudio and API documentation in HTML"
  rm -rf ${ROOTDIR}/docs/html
  cd ${ROOTDIR}/docs
  make html
  cd ${ROOTDIR}
  
  if [[ -d ${ROOTDIR}/docs/_build/html ]]; then
    mv -f ${ROOTDIR}/docs/_build/html ${ROOTDIR}/docs/html
    rm -rf ${ROOTDIR}/docs/_build
  fi
}

# Check if virtual environment is installed and activate
function _activate_py_venv () {
  
  if [[ ! -e ${_VENVPATH}'/bin/activate' ]]; then
    echo "ERROR: Python virtual environment not installed (correctly)"
    echo "ERROR: Unable to activate it, not activation script at ${_VENVPATH}/bin/activate"
    exit 1
  fi
  
  if [[ $_PY_VENV_ACTIVE -eq 0 ]]; then
    source ${_VENVPATH}'/bin/activate'
    _PY_VENV_ACTIVE=1
  fi
}

# ========== MAIN ========== 

echo ""
echo "==== LIEStudio installer script ===="
echo "Date: $( date )"
echo "User: $( whoami )"
echo "System: $( uname -a )"
echo "===================================="
echo ""

cd $ROOTDIR

# 1) Resolve Python version and virtual env options
_resolve_python_version
_resolve_python_venv

# 2) Check directory structure
_check_dir_structure

# 3) Run package install and setup
[[ -z $_PY_VENV ]] && echo "ERROR: no Python venv tools defined", exit 1
if [[ $SETUP -eq 1 ]]; then
  _setup_venv
fi

# 4) Compile software documentation
if [[ $COMPILE_DOCS -eq 1 ]]; then
  _activate_py_venv
  _compile_python_sphinx_docs
fi

# 5) Run Python unittests
if [[ $TEST -eq 1 ]]; then
  
  _activate_py_venv
  
  for component in $( ls -d components/*/ ); do
    if [[ -e ${component}test.py ]]; then
      
      echo "INFO: Run Python unittest for component: $component"
      $_PYTHON_PATH -m unittest -v ${component}test.py
      
    fi
  done
  
fi

# Deactivate Python venv
deactivate >/dev/null 2>&1

# Finish
echo "NOTE: installation succesful"
exit 0
