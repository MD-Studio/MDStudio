#!/usr/bin/env bash

# Terminate standalone microservices based on pid file
if [[ -e standalone.pid ]]; then

	while IFS= read -r pid; do
		echo "Stopping standalone service: ${pid}"
		kill ${pid}
	done < standalone.pid

	rm standalone.pid
fi

# stop docker components
docker-compose down
