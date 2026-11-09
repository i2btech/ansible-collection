"""
Util class for cloudflare_bulk_redirects_restore
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import csv
import json
import time
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import fetch_url

MAX_ALLOWED_REDIRECTS = 100

error_messages = {
    'file_not_found': 'File `{filename}` was not found.',
    'cf_api_error': 'Cloudflare API error during {action}: {error}',
}


class CloudflareBulkRestoreHelper:
    """
    Class CloudflareBulkRestoreHelper
    Handles purging current Cloudflare List items and restoring them from a backup CSV.
    """

    CF_API_ENDPOINTS = {
        'account': 'https://api.cloudflare.com/client/v4/accounts/{account_id}',
        'list_items': 'https://api.cloudflare.com/client/v4/accounts/{account_id}/rules/lists/{list_id}/items',
        'operation_status': 'https://api.cloudflare.com/client/v4/accounts/{account_id}/rules/lists/bulk_operations/{operation_id}',
    }

    def __init__(self, module):
        self.module = module
        self.account_id = module.params['cloudflare_account']
        self.api_token = module.params['cloudflare_api_token']
        self.list_id = module.params.get('cloudflare_list_id')
        self.backup_filename = module.params.get('cloudflare_backup_filename')
        self.force_bulk = module.params.get('force_bulk', False)

        self.payload_restore = []

    @staticmethod
    def cloudflare_bulk_restore_argument_spec():
        """
        Define default arguments for restoration modules
        """
        return dict(
            cloudflare_account=dict(
                type='str',
                required=True,
                no_log=False),
            cloudflare_api_token=dict(
                type='str',
                required=True,
                no_log=True),
            cloudflare_list_id=dict(
                type='str',
                required=True),
            cloudflare_backup_filename=dict(
                type='str',
                required=True),
            force_bulk=dict(
                type='bool',
                default=False,
                required=False),
            validate_certs=dict(
                type='bool',
                default=True),
            use_proxy=dict(
                type='bool',
                default=True),
            sleep=dict(
                type='int',
                default=1),
            retries=dict(
                type='int',
                default=3),
        )

    def request(self, api_url, method, data=None, headers=None):
        """
        Generic HTTP request method using Ansible fetch_url
        """
        headers = headers or {}
        headers.update({
            'Authorization': f'Bearer {self.api_token}'
        })

        if isinstance(data, (dict, list)):
            data = self.module.jsonify(data)

        retries = 1
        while retries <= self.module.params['retries']:
            response, info = fetch_url(
                module=self.module,
                url=api_url,
                method=method,
                headers=headers,
                data=data,
                use_proxy=self.module.params['use_proxy']
            )

            if info is not None and info['status'] != -1:
                break

            time.sleep(self.module.params['sleep'])
            retries += 1

        content = {}
        if response is not None:
            body = to_text(response.read())

            if body:
                try:
                    content = json.loads(body)
                except ValueError:
                    content['content'] = body

        if info.get('status', 200) >= 400 and not content.get('errors'):
            content['errors'] = [f"HTTP {info.get('status')}: {info.get('msg', 'Unknown error')}"]

        return info, content

    def verify_credentials(self):
        """
        Verify API credentials and connection against Cloudflare API.
        """
        url = self.CF_API_ENDPOINTS['account'].format(account_id=self.account_id)
        _, response_json = self.request(url, method='GET')

        if not response_json.get('success'):
            self.module.fail_json(
                msg=error_messages['cf_api_error'].format(
                    action='VERIFY_CREDENTIALS', error=response_json.get('errors')
                )
            )
        return response_json

    def get_all_existing_item_ids(self):
        """
        Fetch all current item IDs from the Cloudflare list so they can be wiped.
        """
        item_ids = []
        cursor = None
        per_page = 100

        while True:
            url = f"{self.CF_API_ENDPOINTS['list_items'].format(account_id=self.account_id, list_id=self.list_id)}?per_page={per_page}"
            if cursor:
                url += f"&cursor={cursor}"

            _, response_json = self.request(url, method='GET')

            if not response_json.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='GET_ITEMS_FOR_PURGE', error=response_json.get('errors')
                    )
                )

            result = response_json.get('result', [])
            if not result:
                break

            for item in result:
                if 'id' in item:
                    item_ids.append({"id": item['id']})

            cursor = response_json.get('result_info', {}).get('cursors', {}).get('after')
            if not cursor:
                break

        return item_ids

    def read_backup_file(self):
        """
        Read backup CSV file and build POST payload for restoration.
        """
        try:
            filepath = self.backup_filename
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.getcwd(), filepath)

            self.payload_restore = []

            with open(filepath, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header

                for row in reader:
                    if not row or not any(field.strip() for field in row):
                        continue

                    if len(row) < 2:
                        self.module.fail_json(
                            msg=f"Formato de CSV de backup inválido en '{self.backup_filename}'. "
                                f"Se esperaban al menos 2 columnas (origen, destino), pero se detectó: {row}"
                        )

                    preserve_query_string = True
                    if len(row) >= 3 and row[2].strip():
                        preserve_query_string = self.parse_bool(row[2])

                    source = row[0].strip()
                    target = row[1].strip()

                    self.payload_restore.append({
                        "redirect": {
                            "source_url": source,
                            "target_url": target,
                            "status_code": 301,
                            "preserve_query_string": preserve_query_string
                        }
                    })

            total_items = len(self.payload_restore)

            if total_items > MAX_ALLOWED_REDIRECTS and not self.force_bulk:
                self.module.fail_json(
                    msg=f"SAFETY STOP: Attempting to restore {total_items} redirects from backup, "
                        f"which exceeds the safety threshold of {MAX_ALLOWED_REDIRECTS}. "
                        f"To bypass this check, set 'force_bulk: true' in your Ansible task options."
                )

        except FileNotFoundError:
            self.module.fail_json(
                msg=error_messages['file_not_found'].format(filename=self.backup_filename)
            )

        except Exception as e:
            self.module.fail_json(msg=f"Unexpected error while reading backup file: {str(e)}")

    def restore_bulk_list(self):
        """
        Purge all existing items in Cloudflare and restore from the backup CSV payload.
        """
        self.read_backup_file()

        url = self.CF_API_ENDPOINTS['list_items'].format(
            account_id=self.account_id,
            list_id=self.list_id
        )

        # 1. Obtener y purgar todos los registros existentes en Cloudflare
        existing_item_ids = self.get_all_existing_item_ids()

        if existing_item_ids:
            _, res_del = self.request(url, method='DELETE', data={"items": existing_item_ids})

            if not res_del.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='PURGE_BEFORE_RESTORE', error=res_del.get('errors')
                    )
                )

            op_id = res_del['result']['operation_id']
            self.wait_for_operation(op_id)

        # 2. Insertar los ítems restaurados del backup
        if self.payload_restore:
            _, res_post = self.request(url, method='POST', data=self.payload_restore)

            if not res_post.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='POST_RESTORE', error=res_post.get('errors')
                    )
                )

            op_id = res_post['result']['operation_id']
            self.wait_for_operation(op_id)

        return True

    def wait_for_operation(self, operation_id):
        """
        Wait until a Cloudflare bulk operation finishes processing.
        """
        while True:
            status = self.operation_status(operation_id)
            state = status.get('result', {}).get('status')

            if state == 'completed':
                break

            if state == 'failed':
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='BULK_OP', error=status.get('errors')
                    )
                )

            time.sleep(self.module.params['sleep'])

    def operation_status(self, operation_id):
        """
        Fetch current status of an asynchronous bulk operation.
        """
        url = self.CF_API_ENDPOINTS['operation_status'].format(
            account_id=self.account_id,
            operation_id=operation_id
        )
        _, content = self.request(url, method='GET')
        return content

    @staticmethod
    def parse_bool(value):
        """
        Safely convert string representations to boolean values.
        """
        if isinstance(value, bool):
            return value

        clean_val = str(value).strip().lower()
        return clean_val in ("true", "1", "yes", "y", "t")