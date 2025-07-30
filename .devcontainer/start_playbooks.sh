#!/bin/bash

echo $INVENTORY | base64 -d > aws_ec2.yaml
echo $PLAYBOOK | base64 -d > playbook.yml
echo $SSH_KEY | base64 -d > ssh.key
chmod 400 ssh.key

/home/ubuntu/.local/bin/ansible-playbook -i aws_ec2.yaml -u $SSH_USER --private-key ssh.key playbook.yml
