#! /bin/bash

pipenv install --skip-lock pipenv
pipenv install --skip-lock

echo "Starting component $COMPONENT"
trap 'pkill python' SIGTERM
pipenv run python -u -m "$COMPONENT"
