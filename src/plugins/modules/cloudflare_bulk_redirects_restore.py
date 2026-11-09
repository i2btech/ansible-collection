#!/usr/bin/python
# -*- coding: utf-8 -*-
""" cloudflare_bulk_redirects_restore module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_bulk_redirects_restore
short_description: Restore Cloudflare Bulk Redirect Lists from Backup CSV
version_added: "1.0.0"
description:
    - Restores a Cloudflare Bulk Redirect List to a previous state by loading items from a CSV backup file.
    - Purges all existing redirect items from the specified Cloudflare list prior to populating the restored items.
    - Enforces safety limit checks unless explicitly overridden with C(force_bulk: true).
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
            - ID of the target Cloudflare Bulk Redirect List to restore.
        type: str
        required: true
    cloudflare_backup_filename:
        description:
            - Path to the local CSV backup file to restore into Cloudflare.
        type: str
        required: true
    force_bulk:
        description:
            - Bypass safety limit validation to allow restoring large redirect sets.
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
            - Number of seconds to wait between retries or polling status.
        type: int
        default: 1
    retries:
        description:
            - Number of times to retry the request in case of connection failures.
        type: int
        default: 3
notes:
    - The CSV backup file path is relative to the directory where the playbook is executed.
    - In check mode, no API calls are made and the module reports C(changed=false).
    - If restoring more than 100 redirects, C(force_bulk: true) must be explicitly set.
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: Restore Cloudflare bulk redirects from local CSV backup file
  i2btech.ops.cloudflare_bulk_redirects_restore:
    cloudflare_account: "{{ cloudflare_account }}"
    cloudflare_api_token: "{{ cloudflare_api_token }}"
    cloudflare_list_id: "abc123xyz456"
    cloudflare_backup_filename: "20260330_120000_backup_list_bulk_redirects.csv"
    force_bulk: true
'''

RETURN = r'''
changed:
    description: Whether the Cloudflare bulk list was purged and restored.
    type: bool
    returned: always
msg:
    description: Success message details.
    type: str
    returned: always
    sample: "Bulk redirects restored successfully from backup file"
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.cloudflare_bulk_restore import CloudflareBulkRestoreHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position


def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module
    module_args = CloudflareBulkRestoreHelper.cloudflare_bulk_restore_argument_spec()

    result = dict(
        changed=False,
        failed=False,
        message=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    restore_helper = CloudflareBulkRestoreHelper(module)

    restore_helper.verify_credentials()
    status = restore_helper.restore_bulk_list()

    if status:
        module.exit_json(changed=True, msg="Bulk redirects restored successfully from backup file")
    else:
        module.exit_json(changed=False, msg="No items to restore or operation bypassed.")


def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()