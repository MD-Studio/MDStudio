#!/usr/bin/env bash

export WORKDIR=/tmp/mdstudio
export MD_CONFIG_ENVIRONMENTS=dev,docker

# Docker based Services
SERVICES=("lie_amber" "lie_atb" "lie_plants_docking" "lie_pylie" "lie_structures")

# Services install locally with pip
STANDALONE_SERVICES=( "lie_md" )

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
    pip install "https://github.com/MD-Studio/${x}/tarball/master#egg=${x}"
    echo "Registering component: ${x}"
    python -m $x & > /dev/null 2>&1
done
