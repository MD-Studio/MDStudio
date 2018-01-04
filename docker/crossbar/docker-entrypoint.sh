#! /bin/bash

if [ ! -f /root/.cache/.firstrun-docker ]; then
    pipenv install --skip-lock --sequential
fi

touch /root/.cache/.firstrun-docker

trap 'pkill crossbar' SIGTERM

pipenv run python -u .
