#!/usr/bin/env bash
# build the docker containers
docker-compose build

# allows polling the installation process
rm docker/.INSTALLING 2> /dev/null
touch docker/.INSTALLING
chmod 777 docker/.INSTALLING

# for documentation
mkdir -p docs/html 
mkdir -p docs/html/_static

mkdir -p .pycharm_helpers

docker-compose stop

# start the containers
docker-compose up -d

# login into workspace
if [ $OSTYPE == 'msys' ]; then
    winpty docker exec -it liestudio_workspace_1 bash -l
else
    docker exec -it liestudio_workspace_1 bash -l
fi
