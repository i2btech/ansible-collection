FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN \
  apt update && \
  apt install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    curl \
    openssh-client \
    mariadb-client \
    ca-certificates \
    logrotate \
    sudo \
    zip \
    unzip && \
  apt clean && \
  apt autoremove --purge

RUN \
    mkdir -p /home/ubuntu/.vscode-server/extensions && \
    chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server

RUN \
  echo "ubuntu   ALL=(ALL:ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/ubuntu > /dev/null && \
  chmod 440 /etc/sudoers.d/ubuntu

USER ubuntu

COPY ../src/requirements.txt /home/ubuntu/requirements.txt
COPY ../src/requirements-gallaxy.yml /home/ubuntu/requirements-gallaxy.yml
RUN \
  pip3 -q install -r /home/ubuntu/requirements.txt --break-system-packages --no-warn-script-location && \
  pip3 cache purge && \
  /home/ubuntu/.local/bin/ansible-galaxy install -r /home/ubuntu/requirements-gallaxy.yml

COPY --chown=ubuntu:ubuntu --chmod=755 .devcontainer/start.sh /home/ubuntu/start.sh

WORKDIR /workspace/src
ENTRYPOINT ["/home/ubuntu/start.sh"]
