#!/usr/bin/env bash

# Make sure the installation output is clean
rm /tmp/.INSTALLINGDONE
rm /tmp/.INSTALLING

user=$(ls -ld /app | awk '{print $3}')
group=$(ls -ld /app | awk '{print $4')

# check if the mounted filesystem is NTFS
touch /app/.isntfs
chmod /app/.isntfs 755
chmod /app/.isntfs 777

if [ $(stat -c %a /app/.isntfs) == '755' ]; then
    user=1000
    group=1000

    echo "Detected NTFS mount on /app, enabling usermode" >> /tmp/.INSTALLING
fi
rm /app/.isntfs

if [ "$user" != "root" ]; then

    uid=$(id -u $user 2> /dev/null || echo -1)
    if [ $uid -lt 0 ]; then
        uid=$user
        gid=$(cut -d: -f3 < <(getent group $group))
        if [ "$gid" == "" ]; then
            gid=$group
            group='liegroup'
            # Initialize liegroup
            echo $(addgroup --gid $(echo $gid) liegroup) >> /tmp/.INSTALLING
        fi

        # Initialize lieuser
        echo $(adduser --uid $(echo $uid) --gid $(echo $gid) --system lieuser) >> /tmp/.INSTALLING
        user="lieuser"

        head ~/.bashrc -n -1 > /tmp/.bashrc
        mv /tmp/.bashrc ~/.bashrc
        sed -i '/alias helpme/d' ~/.bashrc
        echo 'alias helpme="(/app/docker/welcome.sh; /app/docker/welcome-user.sh)"' >> ~/.bashrc
        echo "alias root='touch /tmp/noexit; exit'" >> ~/.bashrc
        cp ~/.bashrc /home/lieuser/.bashrc
        sed -i '/python \/app\/docker\/progress.py/d' /home/lieuser/.bashrc
        chown lieuser /home/lieuser/.bashrc
        echo "helpme" >> /home/lieuser/.bashrc
        echo "alias lieuser='su lieuser -s $(which bash)'" >> ~/.bashrc
        echo "echo 'Switching to user $user'" >> ~/.bashrc
        echo "su lieuser -s $(which bash)" >> ~/.bashrc
        echo "[[ -f /tmp/noexit ]] && rm /tmp/noexit || exit" >> ~/.bashrc
        echo "Default user is now $user" >> /tmp/.INSTALLING
    else
        group='liegroup'
    fi
    user=$(getent passwd "$uid" | cut -d: -f1)
fi

if [[ ! -d "/app/.venv" ]]; then

    if [ "$user" != "root" ]; then
        echo "Running installer.sh as $user" >> /tmp/.INSTALLING
    else
        echo 'Running installer' >> /tmp/.INSTALLING
    fi

    setuser $user ./installer.sh --setup --local-dev &>> /tmp/.INSTALLING
fi

echo 'Enabling debugging code' &>> /tmp/.INSTALLING
# disable the debugger disabling code which spews a LOT of warnings
sed -i 's/ sys.settrace(None)/ #sys.settrace(None)/g' /app/.venv/lib/python2.7/site-packages/twisted/internet/process.py

echo 'Set mongo connection' &>> /tmp/.INSTALLING
sed -i 's/"host": "localhost",/"host": "mongo",/g' /app/data/settings.json

if [ -d /app/.pycharm_helpers/pydev/ ]; then

    if [ "$user" != "root" ]; then
        echo "Compiling as $user" &>> /tmp/.INSTALLING
    else
        echo 'Compiling pycharm helpers' &>> /tmp/.INSTALLING
    fi
    setuser $user python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> /tmp/.INSTALLING
fi

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> /tmp/.INSTALLING

#execute the default phusion script
/sbin/my_init