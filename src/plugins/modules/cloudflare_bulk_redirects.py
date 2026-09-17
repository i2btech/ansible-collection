#!/usr/bin/python
# -*- coding: utf-8 -*-
""" cloudflare_bulk_redirects module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_bulk_redirects
short_description: Manage Cloudflare Bulk Redirect Lists
version_added: "1.0.0"
description:
    - Manage and synchronize Cloudflare Bulk Redirect Lists by reading target/source pairs from a CSV file.
    - Fetch existing rules from the specified list, delete items that need replacement, and create new redirect items.
    - Handles asynchronous operations from Cloudflare until they complete successfully.
options:
    cloudflare_account:
        description:
            - Account ID of the Cloudflare account.
        type: str
        required: true
    cloudflare_api_token:
        description:
            - API token used for authentication with Cloudflare API.
        type: str
        required: true
    cloudflare_list_id:
        description:
            - ID of the target Cloudflare Bulk Redirect List to update.
        type: str
        required: true
    cloudflare_filename:
        description:
            - Name of the CSV file containing the source and target URL pairs.
        type: str
        required: true
    replace_existing:
        description:
            - Whether to replace/update items in the Cloudflare list if the source URL already exists.
        type: bool
        default: false
    validate_certs:
        description:
            - Whether to validate SSL certificates when contacting the Cloudflare API.
        type: bool
        default: true
    use_proxy:
        description:
            - Whether to use system proxies when making HTTP requests to the Cloudflare API.
        type: bool
        default: true
    sleep:
        description:
            - Number of seconds to wait between retries.
        type: int
        default: 5
    retries:
        description:
            - Number of times to retry the request in case of connection failures.
        type: int
        default: 3
notes:
    - The CSV file path is relative to the directory where the playbook is executed (typically at the same level as the playbook).
    - In check mode, no API calls are made and the module reports C(changed=false).
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: Synchronize bulk redirects to Cloudflare
  i2btech.ops.cloudflare_bulk_redirects:
    cloudflare_account: "{{ cloudflare_account }}"
    cloudflare_api_token: "{{ cloudflare_api_token }}"
    cloudflare_list_id: "abc123xyz456"
    cloudflare_filename: "redirects.csv"
    replace_existing: true
'''

RETURN = r'''
changed:
    description: Whether the Cloudflare bulk list was modified.
    type: bool
    returned: always
msg:
    description: Success message details.
    type: str
    returned: always
    sample: "Bulk redirects updated successfully"
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.cloudflare_bulk import CloudflareBulkHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position

def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module

    module_args = CloudflareBulkHelper.cloudflare_bulk_argument_spec()

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

    bulk = CloudflareBulkHelper(module)

    bulk.verify_credentials()
    status = bulk.add_item_bulk_list()

    if status:
        module.exit_json(changed=True, msg="Bulk redirects updated successfully")
    else:
        module.exit_json(changed=False, msg="No new or modified redirects to process. Cloudflare list is already up to date.")


def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()
