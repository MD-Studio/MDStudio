FROM python:3.5

RUN apt-get install libssl-dev

RUN pip install pipenv
ENV PIPENV_VENV_IN_PROJECT=1

ADD docker-entrypoint.sh /docker-entrypoint.sh
VOLUME /app
WORKDIR /app

EXPOSE 8080 8000

ENTRYPOINT ["bash", "/docker-entrypoint.sh"]
