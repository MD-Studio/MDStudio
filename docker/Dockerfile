FROM phusion/baseimage:latest

RUN apt-get update && \
    apt-get install -y python2.7 python-pip libffi-dev libssl-dev git sudo curl

RUN curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -- && \
    apt-get install nodejs && \
    npm i -g gulp gulp-cli typescript typings && \
    apt-get clean

RUN pip install --upgrade pip
RUN pip install pipenv

ARG PUID=1000
ARG PGID=1000
RUN groupadd -g $PGID liestudio && \
    useradd -u $PUID -g liestudio -m liestudio

# ssh:
ADD docker/insecure_id_rsa /tmp/id_rsa 
ADD docker/insecure_id_rsa.pub /tmp/id_rsa.pub 

ARG INSTALL_WORKSPACE_SSH=false
ENV INSTALL_WORKSPACE_SSH ${INSTALL_WORKSPACE_SSH}

RUN if [ ${INSTALL_WORKSPACE_SSH} = true ]; then \
    rm -f /etc/service/sshd/down && \
    cat /tmp/id_rsa.pub >> /root/.ssh/authorized_keys \
        && cat /tmp/id_rsa.pub >> /root/.ssh/id_rsa.pub \
        && cat /tmp/id_rsa >> /root/.ssh/id_rsa \
        && rm -f /tmp/id_rsa* \
        && chmod 600 /root/.ssh/authorized_keys /root/.ssh/id_rsa.pub \
    && chmod 400 /root/.ssh/id_rsa \
;fi

ADD docker/.bash_profile ~/.bash_profile

WORKDIR /app/

ENTRYPOINT ["bash", "/app/docker/docker-entrypoint.sh" ] 