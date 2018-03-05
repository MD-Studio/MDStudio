#!/usr/bin/env bash

# Make sure the installation output is clean
rm /tmp/.INSTALLINGDONE
rm /tmp/.INSTALLING

user=$(ls -ld /app | awk '{print $3}')
group=$(ls -ld /app | awk '{print $4}')

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

        sed -i 's/USERMODE=0/USERMODE=1/g' ~/.bashrc
        cp -t /home/lieuser/ ~/.bashrc ~/.bashrc_all ~/.bashrc_user
        chown lieuser /home/lieuser/*
        echo 'source ~/.bashrc_root' >> ~/.bashrc
        echo 'source ~/.bashrc_user' >> /home/lieuser/.bashrc

        echo "Default user is now $user" >> /tmp/.INSTALLING
    else
        group='liegroup'
    fi

    # Get correct user
    user=$(getent passwd "$uid" | cut -d: -f1)
fi
touch /app/docker/.USERDONE

if [[ ! -d "/app/.venv" ]]; then

    if [ "$user" != "root" ]; then
        echo "Running installer.sh as $user" >> /tmp/.INSTALLING
    else
        echo 'Running installer' >> /tmp/.INSTALLING
    fi

    setuser $user ./installer.sh --setup --local-dev &>> /tmp/.INSTALLING
fi

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
