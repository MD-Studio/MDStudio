FROM python:3.6

RUN pip install --upgrade pip pipenv

COPY /docker-entrypoint.sh /docker-entrypoint.sh

VOLUME /app
WORKDIR /app

STOPSIGNAL SIGTERM

CMD ["bash", "/docker-entrypoint.sh"]
