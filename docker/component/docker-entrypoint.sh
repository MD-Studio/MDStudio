#! /bin/bash

cd components/$COMPONENT

if [ ! -f /root/.cache/.firstrun-docker ]; then
    pipenv install --skip-lock --sequential
fi

touch /root/.cache/.firstrun-docker

echo "Starting component $COMPONENT"
trap 'pkill python' SIGTERM
pipenv run bash -c 'cd ../.. && python -u -m "$COMPONENT"'
