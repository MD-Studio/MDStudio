#!/bin/bash

# Setting variable
export MD_CONFIG_ENVIRONMENTS=dev,docker

# install dependencies
for c in $( ls components ); do
    DIR="${PWD}/components/${c}"
    if [ -d ${DIR} ]; then
	pip install -e ${DIR} > /dev/null 2>&1
    fi
done

# Launch services. two times lie_md in roundrobin
SERVICES=( "lie_echo" "lie_md" "lie_structures")

for x in ${SERVICES[@]};do
    echo "Registering component: ${x}"
    python -m $x & > /dev/null 2>&1
done
