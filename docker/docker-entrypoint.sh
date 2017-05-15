#!/usr/bin/env bash
user=$(ls -ld /app | awk '{print $3}')
if [ "$user" != "root" ]; then
    group=$(ls -ld /app | awk '{print $4')

    uid=$(id -u $user 2> /dev/null || echo -1)
    if [ $uid -lt 0 ]; then
        uid=$user
        gid=$(cut -d: -f3 < <(getent group $group))
        if [ "$gid" == "" ]; then
            gid=$group
            group='liegroup'
            echo "Initializing group liegroup with gid=$gid" >> docker/.INSTALLING
            addgroup liegroup --gid $(echo $gid)
        fi

        echo "Initializing user lieuser with uid=$uid, in group $group" >> docker/.INSTALLING
        adduser lieuser --uid $(echo $uid) --gid $(echo $gid) --system
        user="lieuser"

        head ~/.bashrc -n -1 > /tmp/.bashrc
        mv /tmp/.bashrc ~/.bashrc
        echo "alias root='touch /tmp/noexit; exit'" >> ~/.bashrc
        cp ~/.bashrc /home/lieuser/.bashrc
        chown lieuser /home/lieuser/.bashrc
        echo "helpme" >> /home/lieuser/.bashrc
        echo "alias lieuser='su lieuser -s $(which bash)'" >> ~/.bashrc
        echo "echo 'Switching to user $user'" >> ~/.bashrc
        echo "su lieuser -s $(which bash)" >> ~/.bashrc
        echo "[[ -f /tmp/noexit ]] && rm /tmp/noexit || exit" >> ~/.bashrc
        echo "Default user is now $user" >> docker/.INSTALLING
    fi
fi

if [[ ! -d "/app/.venv" ]]; then

    if [ "$user" != "root" ]; then
        echo "Running installer.sh as $user" >> docker/.INSTALLING
    else
        echo 'Running installer' >> docker/.INSTALLING
    fi

    setuser $user bash installer.sh --setup --local-dev &>> docker/.INSTALLING
fi

echo 'Enabling debugging code' &>> docker/.INSTALLING
# disable the debugger disabling code which spews a LOT of warnings
sed -i 's/ sys.settrace(None)/ #sys.settrace(None)/g' /app/.venv/lib/python2.7/site-packages/twisted/internet/process.py

echo 'Set mongo connection' &>> docker/.INSTALLING
sed -i 's/"host": "localhost",/"host": "mongo",/g' /app/data/settings.json

if [ -d /app/.pycharm_helpers/pydev/ ]; then

    if [ "$user" != "root" ]; then
        echo "Compiling as $user" &>> docker/.INSTALLING
    else
        echo 'Compiling pycharm helpers' &>> docker/.INSTALLING
    fi
    setuser $user python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> docker/.INSTALLING
fi

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init