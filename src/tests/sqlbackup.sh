#!/bin/bash

EXTRA_VARS="sql_host=i2btech-core-prd-i2bwebngprd.cmvnulshhnnh.us-east-1.rds.amazonaws.com \
  sql_user=i2bwebngprd_user \
  sql_dbs=i2bwebngprd \
  s3_bucket=i2btech-core-prd-logsrotate \
  s3_prefix=sqlbackup"

ansible-playbook i2btech.ops.sqlbackup --extra-vars "${EXTRA_VARS}"
