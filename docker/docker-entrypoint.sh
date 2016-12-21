if [ ! -d "$DIRECTORY" ]; then
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
else
    bash installer.sh --upgrade &>> docker/.INSTALLING
fi


# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init