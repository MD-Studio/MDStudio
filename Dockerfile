FROM python:2.7

ADD . /app/
WORKDIR /app/

ARG PUID=1000
ARG PGID=1000
RUN groupadd -g $PGID liestudio && \
    useradd -u $PUID -g liestudio -m liestudio

USER liestudio

RUN bash installer.sh --setup