#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: gws_group_checker

short_description: Audit and verify Google Workspace group members

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: 
    - Queries the Google Workspace Directory API to fetch current group members.
    - Compares active members against lists of expected and excluded users.
    - Generates a detailed audit report highlighting missing and unexpected members without failing execution.
    - Fails execution when discrepancies are found.

options:
    credential_file:
        description:
        - Relative or absolute path to the Service Account JSON key file.
        type: str
        required: true
    group_email:
        description:
        - Email address of the targeted Google Workspace group to audit.
        type: str
        required: true
    expected_users:
        description:
        - List of user email addresses expected to be members of the group.
        type: list
        elements: str
        required: true
    excluded_users:
        description:
        - Optional list of user email addresses to ignore during the audit calculation.
        type: list
        elements: str
        required: false
        default: []

author:
    - IT I2B
'''

EXAMPLES = r'''
- name: Audit global organization group members
  i2btech.ops.gws_group_checker:
    credential_file: "credentials.json"
    group_email: "group.user@i2btech.com"
    expected_users: "{{ gws_users | map(attribute='mail') | list }}"
    excluded_users:
        - "user.name@i2btech.com"
          - "other.user@i2btech.com"
  register: group_check

'''

RETURN = r'''
msg:
  description: Summary message of the group membership audit result.
  type: str
  returned: always
  sample: "Verification completed for group.user@i2btech.com: membership discrepancies were found."
missing_users:
  description: List of email addresses present in expected_users but not currently in the group.
  type: list
  elements: str
  returned: success
  sample: ["user.name@i2btech.com"]
unexpected_users:
  description: List of email addresses found in the group but not specified in expected_users.
  type: list
  elements: str
  returned: success
  sample: ["user.name@i2btech.com"]
in_group_count:
  description: Total number of active members detected in the group.
  type: int
  returned: success
  sample: 68
expected_count:
  description: Target number of expected users (calculated as expected_users minus excluded_users).
  type: int
  returned: success
  sample: 70
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.i2btech.ops.plugins.module_utils.google_workspace_group_check import GoogleWorkspaceGroupCheckHelper

def run_module():

    module_args = dict(
        credential_file=dict(type='str', required=True),
        group_email=dict(type='str', required=True),
        expected_users=dict(type='list', elements='str', required=True),
        excluded_users=dict(type='list', elements='str', default=[])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    checker = GoogleWorkspaceGroupCheckHelper(module)
    result = checker.check_membership()

    if result.get("failed", False):
        module.fail_json(**result)
        
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
