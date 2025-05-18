#!/bin/bash

export SQL_HOST="i2btech-core-prd-i2bwebngprd.cmvnulshhnnh.us-east-1.rds.amazonaws.com"
export SQL_USER="i2bwebngprd_user"
export SQL_DBS="i2bwebngprd"
export S3_BUCKET="i2btech-core-prd-logsrotate"
export S3_PREFIX="sqlbackup"

ansible-playbook i2btech.ops.sqlbackup
