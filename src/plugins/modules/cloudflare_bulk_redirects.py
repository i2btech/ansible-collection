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
    - Generates a local backup CSV file and optionally uploads it to Google Drive using impersonation if configured.
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
    cloudflare_backup_filename:
        description:
            - Filename for the local CSV backup created before modifying existing items.
        type: str
        default: "backup_list_bulk_redirects.csv"
        required: false
    target_domain:
        description:
            - Optional canonical domain to force on target URLs (e.g., 'www.example.cl').
        type: str
        required: false
    google_drive_folder_id:
        description:
            - ID of the Google Drive Folder where the backup CSV will be uploaded.
        type: str
        required: false
    google_credential_file:
        description:
            - Path to the JSON service account credential file for Google Drive API.
        type: path
        required: false
    google_impersonated_user:
        description:
            - Email address of the user to impersonate for Domain-Wide Delegation.
        type: str
        required: false
    replace_existing:
        description:
            - Whether to replace/update items in the Cloudflare list if the source URL already exists.
        type: bool
        default: false
    force_bulk:
        description:
            - Bypass safety limit validation (10 redirects) to allow bulk processing of large redirect sets.
        type: bool
        default: false
        required: false
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
    - The CSV file path is relative to the directory where the playbook is executed.
    - In check mode, no API calls are made and the module reports C(changed=false).
    - If processing more than 10 redirects, C(force_bulk: true) must be explicitly set.
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: Synchronize bulk redirects with Google Drive Backup using Impersonation
  i2btech.ops.cloudflare_bulk_redirects:
    cloudflare_account: "{{ cloudflare_account }}"
    cloudflare_api_token: "{{ cloudflare_api_token }}"
    cloudflare_list_id: "abc123xyz456"
    cloudflare_filename: "redirects.csv"
    target_domain: "www.example.cl"
    replace_existing: true
    force_bulk: true
    google_drive_folder_id: "1A2b3C4d5E6f7G8h9I0J"
    google_credential_file: "{{ playbook_dir }}/credential.json"
    google_impersonated_user: "admin@domain.com"
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
