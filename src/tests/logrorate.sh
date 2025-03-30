#!/bin/bash

EXTRA_VARS="service=system \
  logs_directories=/tmp/logs1,/tmp/logs2 \
  s3_bucket=i2btech-core-prd-logsrotate"

ansible-playbook i2btech.ops.logrotate --extra-vars "${EXTRA_VARS}"
