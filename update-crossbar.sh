docker-compose pull
docker-compose run --rm crossbar pipenv install --skip-lock
docker-compose run --rm workspace pipenv install --skip-lock --dev
