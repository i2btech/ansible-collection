#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: gws_user_management

short_description: Manage users in domain

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Create/update, logout, set email signature for specific users or group of users.

options:
    credential_file:
        description:
            - Path to the credential file associated with the service account, we assume the json file is in the same location of the playbook.
        type: str
        required: true
        default: 'credential.json'
    action:
        description:
          - Action to perform: signature|signout
        type: str
        required: true
    used_by:
        description:
          - User in the domain with access to use the service account.
        type: str
        required: false
    signature_folder:
        description:
          - Full path to folder where jinja2 template of signature is located.
          - We use the option 'signature' from the properties of the user to set the filename.
          - The template need to use '.j2' extension
        type: str
        required: false
    users_definition:
        description:
            - A list of users that exists in the domain.
        type: list
        elements: dict
        required: false
        default: []
    groups_definition:
        description:
            - A list of groups that exists in the domain.
        type: list
        elements: dict
        required: false
        default: []
    users:
        description:
          - A list of users to update their signature.
        type: list
        elements: str
        required: false
    groups:
        description:
          - A list of groups to update their signature.
        type: list
        elements: str
        required: false

author:
    - IT I2B
'''

EXAMPLES = r'''
- name: Test action signout
    i2btech.ops.gws_user_management:
    action: "signout"
    used_by: "admin@i2btech.com"
    users:
        - "user@i2btech.com"
    groups:
        - "group@i2btech.com"
    tags: signout

- name: Test action signature
    i2btech.ops.gws_user_management:
    action: "signature"
    users_definition: "{{ gws_users }}"
    groups_definition: "{{ gws_groups }}"
    signature_folder: "{{ playbook_dir }}/templates/signatures"
    users:
        - "user.name@i2btech.com"
    groups:
        - "group.users@i2btech.com"
    tags: signature
- name: Test action create_update
    i2btech.ops.gws_user_management:
    action: "create_update"
    used_by: "admin@i2btech.com"
    users_definition: "{{ gws_users }}"
    groups_definition: "{{ gws_groups }}"
    users:
        - "user.name@i2btech.com"
    tags: create_update
'''

RETURN = r'''
message:
    description: Message associated with result of the action.
    type: str
    returned: always
    sample: 'Signatures updated'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.i2btech.ops.plugins.module_utils.google_workspace_user import GoogleWorkspaceUserHelper

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        credential_file=dict(type="str", default="credential.json"),
        action=dict(type="str", required=True),
        used_by=dict(type="str", required=False),
        signature_folder=dict(type="str", required=False),
        users_definition=dict(type="list", required=False, elements="dict"),
        groups_definition=dict(type="list", required=False, elements="dict"),
        users=dict(type="list", elements="str", required=False, default=[]),
        groups=dict(type="list", elements="str", required=False, default=[])
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

    gws = GoogleWorkspaceUserHelper(module)
    result_action = {
        "changed": False,
        "failed": False,
        "message": []
    }

    if module.params['action'] == "signature":
        result_action = gws.set_signature()
    if module.params['action'] == "signout":
        result_action = gws.signout()
    if module.params['action'] == "create_update":
        result_action = gws.create_update()

    result['message'] = result_action["message"]
    result['changed'] = result_action["changed"]
    result['failed'] = result_action["failed"]


    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if result['failed']:
        module.fail_json(msg='An error occur', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
