#!/bin/bash

EXTRA_VARS=$(cat <<EOF
{
  "host": "worker",
  "service": "system",
  "logs_directory": "/tmp/logs",
  "logs_files": [
    "alternatives.log",
    "bootstrap.log",
    "dpkg.log"
  ],
  "s3_bucket": "i2btech-core-prd-logsrotate",
  "s3_prefix": "collection-testing/system"
}
EOF
)

ansible-playbook i2btech.ops.logrotate --extra-vars "${EXTRA_VARS}"
