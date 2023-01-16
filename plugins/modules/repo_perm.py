#!/usr/bin/python
# -*- coding: utf-8 -*-
""" repo_perm module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: repo_perm
short_description: Manage permissions for a repository on Bitbucket Cloud
version_added: "1.0.0"
description:
    - Manage permissions for a repository on Bitbucket Cloud
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
    permissions:
        description: List of permissions that will be granted
        type: list
        elements: dict
        required: true
        suboptions:
            type:
                type: str
                description:
                - Type of member to grant permission
                - Currently we only support type group
                choices: [ group, user ]
                required: true
            name:
                type: str
                description:
                - Name of group or user
                required: true
            permission:
                type: str
                description:
                - Type of permission that will be granted
                choices: [ admin, write, read ]
                required: true
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Set permissions for repository X"
  i2btech.bitbucket.repo_perm:
  username: "alice"
  password: "app_password"
  repository: "example-X"
  permissions:
    - type: group
      name: administrators
      permission: admin
    - type: group
      name: developers
      permission: write
'''

RETURN = r'''
message:
    description: Placeholder for return value
    type: dict
    returned: always
    sample: []
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.bitbucket.plugins.module_utils.bitbucket import BitbucketHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position

def manage_permissions(result, bitbucket, module):
    """ CRUD repo permissions """

    # get current groups assigned to the repo
    current_groups = bitbucket.get_repository_permissions_info(scope='group')
    # get new groups assigned to the repo
    new_groups = []
    for perm in module.params['permissions']:
        if perm['type'] == 'group':
            new_groups.extend([perm])

    # actions for new groups
    for i in new_groups:
        group_exists = False
        group_perm = None
        for x in current_groups:
            if i['name'].lower() == x['name'].lower():
                group_exists = True
                group_perm = x['perm'].lower()
                break

        if group_exists:
            # group exists on current groups, update permissions if they are different
            if not i['perm'].lower() == group_perm:
                bitbucket.apply_repository_permissions('promote', 'group', i['name'], i['perm'])
                result['changed'] = True
        else:
            # group doesn't exist on current groups, add
            bitbucket.apply_repository_permissions('promote', 'group', i['name'], i['perm'])
            result['changed'] = True

    # action for current groups
    for i in current_groups:
        if not any(
            i['name'].lower() == x['name'].lower()
                for x in new_groups
        ):
            # current group doesn't exists on new groups, delete
            bitbucket.apply_repository_permissions('demote', 'group', i['name'])
            result['changed'] = True

def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module

    perm_spec = dict(
        type=dict(
            required=True,
            type='str',
            choices=['user', 'group']),
        name=dict(
            required=True,
            type='str'),
        perm=dict(
            required=False,
            type='str',
            choices=['admin', 'write', 'read'])
    )

    module_args = BitbucketHelper.bitbucket_argument_spec()
    module_args.update(
        repository=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['name']),
        permissions=dict(
            type='list',
            elements='dict',
            required=False,
            no_log=False,
            options=perm_spec),
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

    existing_repository = bitbucket.get_repository_info()

    if existing_repository:
        manage_permissions(result, bitbucket, module)
    else:
        module.fail_json(msg="Repository doesn't exists")

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
