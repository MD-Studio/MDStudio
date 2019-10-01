#!/usr/bin/env bash

docker-compose pull
docker-compose run --rm crossbar pip-sync requirements.txt
docker-compose run --rm workspace pip-sync requirements-dev.txt
