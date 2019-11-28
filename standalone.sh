#!/usr/bin/env bash

export WORKDIR=/tmp/mdstudio
export MD_CONFIG_ENVIRONMENTS=dev,docker

# Docker and standalone services
SERVICES=("mdstudio_structures" "mdstudio_smartcyp" "mdstudio_atb" "mdstudio_amber" "mdstudio_propka")
STANDALONE_SERVICES=( "lie_md" "lie_cli" )
MDSTUDIO_LOGS=$( pwd )"/logs"
MDSTUDIO_PYTHON=$( which python )

# Create temporate files directory for services
ALL_SERVICES=(${SERVICES[@]} ${STANDALONE_SERVICES[@]})
for s in ${ALL_SERVICES[@]}; do
    mkdir -p ${WORKDIR}/${s}
done

# start docker microservices
docker-compose up -d crossbar common_resources
docker-compose up -d ${SERVICES[@]}
exit

# Start standalone components locally
# These are expected to have been installed locally by the user
# Store process PID's in a local file to be used by MDStudio's 'stop.sh' script to
# terminate standalone services.

# Remove PID file
if [[ -e standalone.pid ]]; then
	rm standalone.pid
fi

# Start standalone components locally
for service in ${STANDALONE_SERVICES[@]}; do

    ${MDSTUDIO_PYTHON} -u -m ${service} >> ${MDSTUDIO_LOGS}"/standalone.log" &
	spid=$!
	echo ${spid} >> standalone.pid
    echo "Starting ${service} as standalone component status code: $? PID: ${spid}"

done
