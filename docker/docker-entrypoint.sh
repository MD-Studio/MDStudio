rm docker/.INSTALLING
touch docker/.INSTALLING
chmod 777 docker/.INSTALLING

mkdir docs/html
bash installer.sh --setup &>> docker/.INSTALLING

echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

tail -F -n0 /etc/hosts