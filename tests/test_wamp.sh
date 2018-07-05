#!/bin/bash

export WORKDIR=/tmp/mdstudio
export MD_CONFIG_ENVIRONMENTS=dev,docker

pip install -e ../mdstudio/.[test]
python test_components.py
