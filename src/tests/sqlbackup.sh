#!/bin/bash

export SQL_TYPE="postgresql"
export SQL_HOST="i2btechcoreprdkanban.cmvnulshhnnh.us-east-1.rds.amazonaws.com"
export SQL_USER="manager"
export SQL_DBS="i2btechcoreprdkanban"
export SQL_PASS="__change_me__"
# export S3_BUCKET="i2btech-core-prd-logsrotate"
# export S3_PREFIX="sqlbackup"

ansible-playbook i2btech.ops.sqlbackup
