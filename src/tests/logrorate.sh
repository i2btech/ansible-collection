#!/bin/bash

export SERVICE="system"
export LOGS_DIR="/tmp/logs1,/tmp/logs2"
export S3_BUCKET="i2btech-core-prd-logsrotate"

ansible-playbook i2btech.ops.logrotate
