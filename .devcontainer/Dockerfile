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
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
  unzip -qq awscliv2.zip && \
  ./aws/install && \
  rm -rf ./aws && \
  rm -rf awscliv2.zip

RUN \
  echo "ubuntu   ALL=(ALL:ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/ubuntu > /dev/null && \
  chmod 440 /etc/sudoers.d/ubuntu

USER ubuntu

COPY --chown=ubuntu:ubuntu --chmod=755 .devcontainer/start.sh /home/ubuntu/start.sh
COPY ../src/requirements.txt /home/ubuntu/requirements.txt
RUN \
  pip3 -q install -r /home/ubuntu/requirements.txt --break-system-packages --no-warn-script-location && \
  pip3 cache purge

WORKDIR /workspace/src
ENTRYPOINT ["/home/ubuntu/start.sh"]
