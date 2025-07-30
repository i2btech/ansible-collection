#!/bin/bash

export TAG=$(grep ^version src/galaxy.yml | awk '{ print $2 }')
source .devcontainer/.env

docker buildx bake devcontainer

rm -f src/*.tar.gz
docker run \
  --rm \
  -v $PWD:/workspace \
  -w /workspace/src \
  --entrypoint /home/ubuntu/.local/bin/ansible-galaxy \
  i2btech/ansible-collection:devcontainer \
  collection build

docker run \
  --rm \
  -v $PWD:/workspace \
  -w /workspace/src \
  --entrypoint "" \
  i2btech/ansible-collection:devcontainer \
  /home/ubuntu/.local/bin/ansible-galaxy collection publish i2btech-ops-${TAG}.tar.gz --api-key ${ANSIBLE_GALAXY_API_KEY}

docker buildx bake playbooks # --no-cache
docker login -u i2btech
docker push i2btech/ansible-collection:${TAG}
