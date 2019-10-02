#!/usr/bin/env bash

# Terminate standalone microservices based on pid file
if [[ -e standalone.pid ]]; then

	cat standalone.pid | while read pid; do
		echo "Stopping standalone service: ${pid}"
		kill ${pid}
	done

	rm standalone.pid
fi

# stop docker components
docker-compose down
