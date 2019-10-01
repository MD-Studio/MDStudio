#!/usr/bin/env bash

trap 'pkill crossbar' SIGTERM

if [[ ! -f /root/.cache/.firstrun-docker ]]; then
    virtualenv ~/mdstudio
    (source ~/mdstudio/bin/activate && pip install -r requirements.txt)
fi

touch /root/.cache/.firstrun-docker

source ~/mdstudio/bin/activate
python -u .
