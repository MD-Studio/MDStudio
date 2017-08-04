#! /bin/bash

ROOTDIR='/app'
LOCALDEV=1

# Install all LIEStudio component packages and their dependencies using pip
_force_reinstall=''
[[  $UPDATE -eq 1 ]] && _force_reinstall='--upgrade'

_local_install=''
[[  $LOCALDEV -eq 1 ]] && _local_install='-e'

pipInstall="pip install"
anyPackage=0

# Install LIEStudio components using pip
for package in $( ls -d ${ROOTDIR}/components/lie_corelib/ ); do
    if [[ -e ${package}/setup.py ]] && [[ -z "$(pip show $(basename $package))" ]]; then
        echo "INFO: Install LIEStudio Python component ${package}"
        pipInstall="$pipInstall -e ${package}"
        anyPackage=1
    fi
done

# Install LIEStudio components using pip
for package in $( ls -d ${ROOTDIR}/components/*/ ); do
    if [[ -e ${package}/setup.py ]] && [[ -z "$(pip show $(basename $package))" ]] && [[ "$(basename $package)" != "lie_corelib" ]]; then
        echo "INFO: Install LIEStudio Python component ${package}"
        pipInstall="$pipInstall -e ${package}"
        anyPackage=1
    fi
done

if [[ $anyPackage -eq 1 ]]; then
    $pipInstall
fi

echo "Starting component $COMPONENT"
trap 'pkill python' SIGTERM
python -u -m "$COMPONENT"
