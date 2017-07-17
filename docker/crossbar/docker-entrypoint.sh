#! /bin/bash

ROOTDIR='/app'
LOCALDEV=1

# Install all LIEStudio component packages and their dependencies using pip
_force_reinstall=''
[[  $UPDATE -eq 1 ]] && _force_reinstall='--upgrade'

_local_install=''
[[  $LOCALDEV -eq 1 ]] && _local_install='-e'

cd $ROOTDIR

echo 'Installing Pipenv'
pipenv install
source /app/.venv/bin/activate

pipInstall="pip install"
anyPackage=0
[[ -z "$(pip show crossbar)" ]] && echo 'Installing Crossbar' && pipInstall="pip install crossbar" && anyPackage=1

elementIn () {
  local e
  for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 1; done
  return 0
}

ring0=(lie_componentbase lie_db lie_schema lie_auth)
# Install LIEStudio components using pip
for package in $( ls -d ${ROOTDIR}/components/*/ ); do
    if [[ -e ${package}/setup.py ]]; then
        elementIn $(basename ${package}) ${ring0[@]}
        isRing0=$?
        if [[ isRing0 -eq 1 ]] && [[ -z "$(pip show $(basename $package))" ]]; then
            echo "INFO: Install LIEStudio Python component ${package}"
            # pip install $_force_reinstall $_local_install $package
            pipInstall="$pipInstall -e ${package}"
            anyPackage=1
        elif [[ isRing0 -eq 0 ]]; then
            echo "INFO: Python component $(basename ${package}) is not in ring0"
        else
            echo "INFO: Python component ${package} is already installed"
        fi
    fi
done

if [[ $anyPackage -eq 1 ]]; then
    $pipInstall
fi

trap 'pkill crossbar' SIGTERM

echo 'INFO: Starting crossbar'
python -u -m crossbar start --cbdir /app --config /app/data/crossbar/config_modular.json --logdir /app/data/logs --loglevel info
