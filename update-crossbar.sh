docker-compose pull
docker-compose run --rm crossbar pipenv install
docker-compose run --rm workspace pipenv install --dev
