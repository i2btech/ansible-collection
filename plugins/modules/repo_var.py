#!/usr/bin/python
# -*- coding: utf-8 -*-
""" bitbucket_repo_var module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

#pylint: disable=wrong-import-position

# TODO: definir la forma correcta de hacer esto, debería funcionar tanto para
# el caso cuando se llama al script de forma local y cuando se llama desde un playbook
import sys
import os
script_dir = os.path.dirname( __file__ )
mymodule_dir = os.path.join( script_dir, '..', 'module_utils' )
sys.path.append( mymodule_dir )
from bitbucket import BitbucketHelper

from ansible.module_utils.basic import AnsibleModule

#pylint: disable=wrong-import-position

def manage_variables(result, bitbucket, module):
    """ CRUD variables """

    api_url=bitbucket.BITBUCKET_API_ENDPOINTS['repos-pipeline'].format(
                url=module.params['url'],
                workspace='i2b',
                repo_slug=module.params['repository'])

    current_variables = bitbucket.get_variables(api_url + "/variables/")
    new_variables = []
    for var in module.params['variables']:
        new_variables.extend([var])

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
                bitbucket.manage_repository_variables('update', i['name'], i['value'], var_uuid, i['secured'])
                result['changed'] = True
            # if not secured and value are different, update variable
            else:
                if i['value'] != var_value:
                    bitbucket.manage_repository_variables('update', i['name'], i['value'], var_uuid, i['secured'])
                    result['changed'] = True

        else:
            # variable doesn't exist on current variables, add
            bitbucket.manage_repository_variables('create', i['name'], i['value'], None, i['secured'])
            result['changed'] = True

    # action for current variables
    for i in current_variables:
        if not any(
            i['key'].lower() == x['name'].lower()
                for x in new_variables
        ):
            # current variable doesn't exists on new variables, delete
            bitbucket.manage_repository_variables('delete', None, None, i['uuid'], None)
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
            no_log=False,
            aliases=['name']),
        variables=dict(
            type='list',
            elements='dict',
            required=False,
            no_log=False,
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
        manage_variables(result, bitbucket, module)
    else:
        module.fail_json(msg="Repository doesn't exists")

    if result is not None:
        module.exit_json(**result)
    else:
        # in case of an unknown error
        module.exit_json(**result)

def main():
    """ main funtion """

    run_module()


if __name__ == '__main__':
    main()
