#!/usr/bin/env bash

pip-compile --output-file requirements.txt requirements.in
pip-compile --output-file requirements-dev.txt requirements-dev.in requirements.in 
sed -i "s|-e file://$(pwd)|-e .|" requirements.txt
sed -i "s|-e file://$(pwd)|-e .|" requirements-dev.txt

if hash powershell 2>/dev/null; then
    sed -i "s|-e file:///$(echo $(powershell -Command "(Get-Item -Path .).FullName") | tr '\\' '/')|-e .|" requirements.txt;
    sed -i "s|-e file:///$(echo $(powershell -Command "(Get-Item -Path .).FullName") | tr '\\' '/')|-e .|" requirements-dev.txt;
fi
