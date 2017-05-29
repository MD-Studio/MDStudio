FROM phusion/baseimage:latest

RUN apt-get update && \
    apt-get install -y python2.7 python-pip libffi-dev libssl-dev git sudo curl

RUN curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -- && \
    apt-get install nodejs && \
    npm i -g gulp gulp-cli typescript typings bower && \
    apt-get clean

RUN python -m pip install pipenv
RUN python -m pip install green

# ssh:
ADD insecure_id_rsa /tmp/id_rsa 
ADD insecure_id_rsa.pub /tmp/id_rsa.pub 

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

RUN echo "" >> ~/.bashrc && \
    echo 'python /app/docker/progress.py' >> ~/.bashrc && \
    echo 'alias livedocs="(cd /app/docs; /usr/bin/make livehtml)"' >> ~/.bashrc && \
    echo 'alias docs="(cd /app/docs; /usr/bin/make livehtml)"' >> ~/.bashrc && \
    echo 'alias serve="(cd /app/app; /usr/bin/gulp serve)"' >> ~/.bashrc && \
    echo 'alias compile="(cd /app/app; /usr/bin/gulp compile)"' >> ~/.bashrc && \
    echo 'alias helpme="(/app/docker/welcome.sh)"' >> ~/.bashrc && \
    echo 'alias test="(cd /app; green test.py)"' >> ~/.bashrc && \
    echo "" >> ~/.bashrc && \
    echo 'source /app/.venv/bin/activate' >> ~/.bashrc && \
    echo 'export MONGO_HOST=mongo' >> ~/.bashrc && \
    echo 'export IS_DOCKER=1' >> ~/.bashrc && \
    echo 'cd /app' >> ~/.bashrc && \
    echo 'helpme' >> ~/.bashrc


ADD .bash_profile ~/.bash_profile

WORKDIR /app/

ENTRYPOINT ["bash", "/app/docker/docker-entrypoint.sh"]