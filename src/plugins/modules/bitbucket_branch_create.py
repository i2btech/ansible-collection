#!/usr/bin/python
# -*- coding: utf-8 -*-
""" bitbucket_branch_create module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: bitbucket_branch_create
short_description: Manage branches on Bitbucket Cloud
version_added: "1.0.0"
description:
    - Manage branches on Bitbucket Cloud repositories
options:
    username:
        description:
            - Username used for authentication.
        type: str
        required: true
    password:
        description:
            - Password used for authentication.
        type: str
        required: true
    repository:
        description:
            - Repository name.
        type: str
        required: true
    branch_name:
        description:
            - Branch name to create.
        type: str
        required: true
    target_branch:
        description:
            - Target branch or hash to branch off from.
        type: str
        default: master
    state:
        description:
            - Whether the branch should exist or not.
        type: str
        default: present
        choices: [ present ]
        required: true
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Create release branch"
  i2btech.ops.bitbucket_branch_create:
    username: "alice"
    password: "app_password"
    repository: "example-X"
    branch_name: "release/integration"
    target_branch: "master"
    state: "present"
'''

RETURN = r'''
message:
    description: Placeholder for return value
    type: dict
    returned: always
    sample: []
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.bitbucket import BitbucketHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position

def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module

    module_args = BitbucketHelper.bitbucket_argument_spec()
    module_args.update(
        repository=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['name']),
        branch_name=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['branch']),
        target_branch=dict(
            type='str',
            default='master',
            no_log=False),
        state=dict(
            type='str',
            choices=['present'],
            default='present'),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=[]
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

    bitbucket = BitbucketHelper(module)

    if module.params['state'] == 'present':
        if not module.check_mode:
            result['changed'] = bitbucket.create_branch(
                branch_name=module.params['branch_name'],
                target_branch=module.params['target_branch']
            )

    if result is not None:
        module.exit_json(**result)
    else:
        module.exit_json(**result)

def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()
