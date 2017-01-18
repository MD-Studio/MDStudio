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

# start the containers
docker-compose up -d

# display the installation progress
sh -c 'tail -n +0 -f docker/.INSTALLING | { sed "/<<<<COMPLETED>>>>/ q" && kill $$ ;}' && (rm docker/.INSTALLING || true)

# login into workspace
docker exec -it liestudio_workspace_1 bash -l