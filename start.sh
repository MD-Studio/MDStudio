docker-compose up -d --force-recreate

sleep 1
sh -c 'tail -n +0 -f docker/.INSTALLING | { sed "/<<<<COMPLETED>>>>/ q" && kill $$ ;}' && (rm docker/.INSTALLING || true)

docker exec -it liestudio_workspace_1 bash