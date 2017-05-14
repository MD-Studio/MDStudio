#!/usr/bin/env bash
echo 'Running installer' &>> docker/.INSTALLING

        head ~/.bashrc -n -1 > /tmp/.bashrc
        mv /tmp/.bashrc ~/.bashrc
        echo "alias root='touch /tmp/noexit; exit'" >> ~/.bashrc
        chown lieuser /home/lieuser/.bashrc
        echo "helpme" >> /home/lieuser/.bashrc
        echo "alias lieuser='su lieuser -s $(which bash)'" >> ~/.bashrc
        echo "[[ -f /tmp/noexit ]] && rm /tmp/noexit || exit" >> ~/.bashrc

if [[ ! -d "/app/.venv" ]]; then
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
fi

echo 'Enabling debugging code' &>> docker/.INSTALLING
# disable the debugger disabling code which spews a LOT of warnings
sed -i 's/ sys.settrace(None)/ #sys.settrace(None)/g' /app/.venv/lib/python2.7/site-packages/twisted/internet/process.py

echo 'Set mongo connection' &>> docker/.INSTALLING
sed -i 's/"host": "localhost",/"host": "mongo",/g' /app/data/settings.json

echo 'Compiling pycharm helpers' &>> docker/.INSTALLING
if [ -d /app/.pycharm_helpers/pydev/ ]; then
    python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> docker/.INSTALLING
fi

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init