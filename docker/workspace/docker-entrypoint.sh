#! /bin/bash

if [ ! -f /root/.cache/.firstrun-docker ]; then
    pipenv install --skip-lock --dev --sequential
fi

touch /root/.cache/.firstrun-docker
