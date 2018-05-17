#!/usr/bin/env bash
export WORKDIR=/tmp/mdstudio
cp ${PLANTS_BIN} ${WORKDIR}/lie_plants_docking
docker-compose up -d crossbar lie_amber lie_plants_docking  lie_pylie  # lie_structures
