#!/usr/bin/env bash

export WORKDIR=/tmp/mdstudio

# The plants executable cannot be distribute
cp ${PLANTS_BIN} ${WORKDIR}/lie_plants_docking

# start docker microservices
docker-compose up -d crossbar lie_amber lie_atb lie_plants_docking lie_pylie  # lie_structures

# Launch services. two times lie_md in roundrobin
SERVICES=( "lie_md" "lie_structures")

for x in ${SERVICES[@]};do
    pip install "https://github.com/MD-Studio/${x}/tarball/master#egg=${x}"
    echo "Registering component: ${x}"
    python -m $x & > /dev/null 2>&1
done
