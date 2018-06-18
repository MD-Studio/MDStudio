#! /bin/bash

cd components/$COMPONENT

if [ ! -f /root/.cache/.firstrun-docker ]; then
    virtualenv ~/mdstudio
    (source ~/mdstudio/bin/activate && pip-sync requirements.txt)
fi

touch /root/.cache/.firstrun-docker

source ~/mdstudio/bin/activate

echo "Starting component $COMPONENT"
trap 'pkill python' SIGTERM
cd ../.. && python -u -m "$COMPONENT"
