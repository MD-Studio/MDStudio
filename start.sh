#!/usr/bin/env bash
# build the docker containers
docker-compose build

# for documentation
mkdir -p docs/html 
mkdir -p docs/html/_static

mkdir -p .pycharm_helpers

docker-compose stop

# start the containers
docker-compose up -d

echo 'Waiting for user creation'
while [ ! -f docker/.USERDONE ]; do
    sleep 0.2
done

rm docker/.USERDONE

# login into workspace
if [ $OSTYPE == 'msys' ]; then
    winpty docker exec -it liestudio_workspace_1 bash -l
else
    # docker exec -it liestudio_workspace_1 bash -l
    docker exec -it mdstudio_workspace_1 bash -l
fi
