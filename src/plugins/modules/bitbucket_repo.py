#!/usr/bin/python
# -*- coding: utf-8 -*-
""" bitbucket_repo module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: bitbucket_repo
short_description: Manage repositories on Bitbucket Cloud
version_added: "1.0.0"
description:
    - Manage repositories on Bitbucket Cloud
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
    project_key:
        description:
            - Bitbucket project key.
        type: str
        required: true
    state:
        description:
            - Whether the repository should exist or not.
        type: str
        default: present
        choices: [ absent, present ]
        required: true
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Create example repository"
  i2btech.ops.bitbucket_repo:
  username: "alice"
  password: "app_password"
  repository: "example-X"
  project_key: "POC"
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
        project_key=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['project']),
        repository=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['name']),
        state=dict(
            type='str',
            choices=['present', 'absent'],
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

    existing_repository = bitbucket.get_repository_info()

    # Create new repository in case it doesn't exist
    if not existing_repository and (module.params['state'] == 'present'):
        if not module.check_mode:
            result['changed'] = bitbucket.create_repository()
            # TODO: maybe we can check if the pipeline is enabled already, if not, enable
            # Get configuration of pipeline: GET /2.0/repositories/{workspace}/{repo_slug}/pipelines_config
            bitbucket.enable_repository_pipeline()

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
