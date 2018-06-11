docker-compose pull
docker-compose run --rm crossbar pipenv install --skip-lock --sequential
docker-compose run --rm workspace pipenv install --skip-lock --sequential --dev
