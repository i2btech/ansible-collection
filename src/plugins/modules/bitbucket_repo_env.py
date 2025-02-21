#!/usr/bin/python
# -*- coding: utf-8 -*-
""" bitbucket_repo_env module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: bitbucket_repo_env
short_description: Manage deployment environment for a repository on Bitbucket Cloud
version_added: "1.0.0"
description:
    - Manage deployment environment for a repository on Bitbucket Cloud
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
    name:
        type: str
        description:
            - Name of environment
        required: true
    type:
        type: str
        description:
            - Type of deployment environment
        choices: [ Test, Staging, Production ]
        required: true
    variables:
        description: List of variables that will be managed
        type: list
        elements: dict
        required: true
        suboptions:
            name:
                type: str
                description:
                    - Name of the variable
                required: true
            value:
                type: str
                description:
                    - Value of the variable
                required: true
            secured:
                type: bool
                description:
                - If true, variable will be encrypted and masked in the logs
                - If true, the module will always finish with a state of changed. The Bitbucket Cloud API don't allow to check
                the current value of a secured variable thus we need to always update tha value to applies possible changes on the value
                - If false, you need to delete the variable to change it to secured
                required: false
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Set deployment environments for repository X"
  i2btech.ops.bitbucket_repo_env:
  username: "alice"
  password: "app_password"
  repository: "example-X"
  name: Integration
  type: Test
  variables:
    - name: user
      value: user_db
    - name: pass
      value: _super_secret_pass_
      secured: true
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

def manage_environments(result, bitbucket, module):
    """ CRUD environments """

    current_environments = bitbucket.get_repository_environments()
    env_exists = False
    env_uuid = None
    for x in current_environments:
        if module.params['name'].lower() == x['name'].lower() and module.params['type'].lower() == x['environment_type']['name'].lower():
            env_exists = True
            env_uuid = x['uuid']
            break

    if env_exists:
        # environment exists, manage variables associated with it if they exists
        if module.params['variables'] is not None:
            api_url=bitbucket.BITBUCKET_API_ENDPOINTS['repos-deployments'].format(
                        url=module.params['url'],
                        workspace='i2b',
                        repo_slug=module.params['repository'])
            current_variables = bitbucket.get_variables(api_url + "/environments/" + env_uuid + "/variables")
            manage_environment_variables(result, bitbucket, env_uuid, current_variables, module.params['variables'])

    else:
        # environment doesn't exist on current environments, add it
        new_env = bitbucket.manage_repository_environments('create', module.params['name'], module.params['type'])
        env_uuid = new_env['uuid']
        # manage variables associated with it
        if module.params['variables'] is not None:
            manage_environment_variables(result, bitbucket, env_uuid, [], module.params['variables'])
        result['changed'] = True

def manage_environment_variables(result, bitbucket, env_uuid, current_variables, new_variables):
    """ CRUD variables of environment """

    # actions for new variables
    for i in new_variables:
        var_exists = False
        var_value = None
        var_uuid = None
        for x in current_variables:
            if i['name'].lower() == x['key'].lower():
                var_exists = True
                var_uuid = x['uuid']
                if not x['secured']:
                    var_value = x['value']
                break

        if var_exists:
            # always update secured variable
            if var_value is None:
                bitbucket.manage_environment_variables('update', i['name'], i['value'], env_uuid, var_uuid, i['secured'])
                result['changed'] = True
            # if not secured and value are different, update variable
            else:
                if i['value'] != var_value:
                    bitbucket.manage_environment_variables('update', i['name'], i['value'], env_uuid, var_uuid, i['secured'])
                    result['changed'] = True

        else:
            # variable doesn't exist on current variables, add
            bitbucket.manage_environment_variables('create', i['name'], i['value'], env_uuid, None, i['secured'])
            result['changed'] = True

    # action for current variables
    for i in current_variables:
        if not any(
            i['key'].lower() == x['name'].lower()
                for x in new_variables
        ):
            # current variable doesn't exists on new variables, delete
            bitbucket.manage_environment_variables('delete', None, None, env_uuid, i['uuid'], None)
            result['changed'] = True

def run_module():
    """ main module """
    # define available arguments/parameters a user can pass to the module

    variable_spec = dict(
        name=dict(
            required=True,
            type='str',
            no_log=False,),
        value=dict(
            required=True,
            no_log=True,
            type='str'),
        secured=dict(
            required=False,
            type='bool',
            default=False)
    )

    module_args = BitbucketHelper.bitbucket_argument_spec()
    module_args.update(
        repository=dict(
            type='str',
            required=True,
            no_log=False),
        name=dict(
            required=True,
            type='str',
            no_log=False,),
        type=dict(
            required=True,
            type='str',
            no_log=False,
            choices=['Staging', 'Test', 'Production']),
        variables=dict(
            required=False,
            no_log=False,
            type='list',
            elements='dict',
            options=variable_spec),
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
        manage_environments(result, bitbucket, module)
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
