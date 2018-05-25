#!/usr/bin/env bash

export WORKDIR=/tmp/mdstudio

# Docker based Services
SERVICES=("lie_amber" "lie_atb" "lie_plants_docking" "lie_pylie" "lie_structures" "lie_haddock")

# Services install locally with pip
STANDALONE_SERVICES=( "lie_md" "lie_cli" )

# Create temporate files
ALL_SERVICES=(${SERVICES[@]} ${STANDALONE_SERVICES[@]})
for s in ${ALL_SERVICES[@]}; do
    mkdir -p ${WORKDIR}/${s}
done

# The plants executable cannot be distribute
cp ${PLANTS_BIN} ${WORKDIR}/lie_plants_docking

# start docker microservices
docker-compose up -d crossbar ${SERVICES[@]}

# Start standalone components locally
for x in ${STANDALONE_SERVICES[@]};do
    cd ${WORKDIR}/${x}
    echo "installing ${x} as a standalone component!"
    if [ ! -d ${x} ]; then
	git clone git://github.com/MD-Studio/${x}.git --single-branch
    else
	cd ${WORKDIR}/${x}/${x} && git pull
    fi
    pip install -e ${WORKDIR}/${x}/${x} > /dev/null 2>&1
    if [ ${x} != "lie_cli" ]; then
	python -u -m $x > /dev/null 2>&1 &
    fi
done
