docker-compose pull
docker-compose run --rm crossbar pipenv uninstall crossbar
docker-compose run --rm crossbar pipenv install --skip-lock --dev
docker-compose run --rm workspace pipenv install --skip-lock --dev
