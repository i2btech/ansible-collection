#!/usr/bin/python
# -*- coding: utf-8 -*-
""" aws_backup_restore module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_backup_restore
short_description: Manages restoration of AWS Backups
version_added: "1.0.0"
description:
    - Manages restoration of AWS Backups
options:
    aws_region:
        description:
            - ...
        type: str
        required: true
    vault_name:
        description:
            - ...
        type: str
        required: true
    iam_role_restore:
        description:
            - ...
        type: str
        required: true
    resource_type:
        description:
            - ...
        type: str
        required: true
    resource_name:
        description:
            - ...
        type: str
        required: true
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Restore EFS from AWS Backup"
  i2btech.ops.aws_backup_restore:
  aws_region: "us-east-1"
  vault_name: "vault-name"
  iam_role_restore: "arn:aws:iam::xxx:role/role-name"
  resource_type: "resource-type"
  resource_name: "resource-name"
'''

RETURN = r'''
message:
    description: Placeholder for return value
    type: dict
    returned: always
    sample: []
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.aws_backup_restore import AWSBackupRestoreHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position

def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        aws_region=dict(type="str", default="us-east-1"),
        vault_name=dict(type="str", required=True),
        iam_role_restore=dict(type="str", required=True),
        resource_type=dict(type="str", required=True),
        resource_name=dict(type="str", required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        failed=False,
        message=""
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    restored_resource = AWSBackupRestoreHelper(module)
    result_action = {
        "changed": False,
        "failed": False,
        "message": []
    }

    if module.params['resource_type'] == "EFS":
        existing_resource = restored_resource.get_efs_info()

        # Create a new resource in case it doesn't exist
        if not existing_resource:
            result_action = restored_resource.efs_restore()
            result['message'] = result_action["message"]
            result['changed'] = result_action["changed"]
            result['failed'] = result_action["failed"]
            
        else:
            result['message'] = "EFS " + module.params['resource_name'] + " exist."

    elif  module.params['resource_type'] == "S3":
        existing_resource = restored_resource.get_s3_info()

        # Create a new resource in case it doesn't exist
        if not existing_resource:
            result['message'] = "S3 created"
            
        else:
            result['message'] = "S3 " + module.params['resource_name'] + " exist."

    else:
        result['failed'] = True
        result['message'] = "Unknow Resource type: " + module.params['resource_type']

    if result is not None:
        module.exit_json(**result)
    else:
        # in case of an unknown error
        module.exit_json(**result)

def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()
