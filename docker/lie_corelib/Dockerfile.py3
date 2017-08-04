FROM python:3.5

COPY /docker-entrypoint.sh /docker-entrypoint.sh

VOLUME /app
WORKDIR /app

STOPSIGNAL SIGTERM

ENTRYPOINT ["bash", "/docker-entrypoint.sh"]
CMD python -m $COMPONENT
