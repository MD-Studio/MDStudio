FROM phusion/baseimage:latest

RUN apt-get update && \
    apt-get install -y python2.7 python-pip libffi-dev libssl-dev git sudo curl dos2unix

RUN curl -sL https://deb.nodesource.com/setup_7.x | sudo -E bash -- && \
    apt-get install nodejs && \
    npm i -g gulp gulp-cli typescript typings bower && \
    apt-get clean

RUN python -m pip install pipenv
RUN python -m pip install green
RUN python -m pip install bandit

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
    echo 'export USERMODE=0' >> ~/.bashrc && \
    echo 'source ~/.bashrc_all' >> ~/.bashrc


ADD .bash_profile /root/.bash_profile
ADD .bashrc_all   /root/.bashrc_all
ADD .bashrc_root  /root/.bashrc_root
ADD .bashrc_user  /root/.bashrc_user
# Fix permissions
RUN find /root -type f -name ".bashrc*" -exec chmod 644 {} \; && chmod 644 /root/.bash_profile
# Fix line-endings
RUN find /root -type f -name ".bashrc*" -exec dos2unix {} \;

WORKDIR /app/

ENTRYPOINT ["bash", "/app/docker/docker-entrypoint.sh"]