#! /bin/bash

# Cleanup cached requirements 
find . -type d -name "*.egg-info" -exec rm -rf {} \;
find /tmp -type f -name "pipenv*requirement.txt" -exec rm -f {} \;

pipenv install --skip-lock pipenv
pipenv install --skip-lock

echo "Starting component $COMPONENT"
trap 'pkill crossbar' SIGTERM

pipenv run python -u -m crossbar start --cbdir /app --config /app/data/crossbar/config_modular.json --logdir /app/data/logs --loglevel info
