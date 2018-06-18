pip-compile --generate-hashes --output-file requirements.txt requirements.in
pip-compile --generate-hashes --output-file requirements-dev.txt requirements-dev.in requirements.in 