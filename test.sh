#!/usr/bin/env bash
ROOTDIR=`pwd -P`
_VENVPATH=${ROOTDIR}/.venv

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

  
_activate_py_venv

python tests/test.py  

deactivate >/dev/null 2>&1