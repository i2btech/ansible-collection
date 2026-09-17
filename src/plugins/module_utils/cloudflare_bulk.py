"""
Util class for cloudflare_bulk_redirects
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import csv
import json
import time
from urllib.parse import urlencode, urlparse
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import fetch_url

#
# class: CloudflareBulkHelper
#

error_messages = {
    'file_not_found': 'File `{filename}` was not found.',
    'cf_api_error': 'Cloudflare API error during {action}: {error}',
}

class CloudflareBulkHelper:
    """
    Class CloudflareBulkHelper
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
        self.filename = module.params.get('cloudflare_filename')
        self.replace_existing = module.params.get('replace_existing', False)

        self.payload_post = []
        self.payload_put = []

    @staticmethod
    def cloudflare_bulk_argument_spec():
        """
        Define default arguments for modules
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
            cloudflare_filename=dict(
                type='str',
                required=True),
            replace_existing=dict(
                type='bool',
                default=False),
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

    def read_file(self):
        """
        Read CSV file and build payloads for POST and PUT
        """
        try:
            existing_items = self.get_items_list()
            local_sources = set()

            filepath = self.filename
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.getcwd(), filepath)

            with open(filepath, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)

                for row in reader:
                    if not row or len(row) < 2:
                        continue

                    if len(row) < 3 or not row[2].strip():
                        preserve_query_string = True
                    else:
                        preserve_query_string = self.parse_bool(row[2])

                    source = self.format_source_url(row[0].strip())
                    target = self.format_target_url(row[1].strip())

                    if self.is_home(source) or source in local_sources:
                        continue

                    local_sources.add(source)

                    item_data = {
                        "redirect": {
                            "source_url": source,
                            "target_url": target,
                            "status_code": 301,
                            "preserve_query_string": preserve_query_string
                        }
                    }

                    if source in existing_items:
                        if self.replace_existing:
                            item_data["id"] = existing_items[source]
                            self.payload_put.append(item_data)
                    else:
                        self.payload_post.append(item_data)
                        
        except FileNotFoundError:
            self.module.fail_json(
                msg=error_messages['file_not_found'].format(filename=self.filename)
            )

        except Exception as e:
            self.module.fail_json(msg=f"Unexpected error while reading file: {str(e)}")

    def add_item_bulk_list(self):
        """
        Add or update items in bulk to the Cloudflare List.
        """
        self.read_file()

        if not self.payload_post and not self.payload_put:
            return False

        
        url = self.CF_API_ENDPOINTS['list_items'].format(
            account_id=self.account_id,
            list_id=self.list_id
        )

        if self.payload_put:
            items_to_delete = [{"id": item["id"]} for item in self.payload_put]
            info, res_del = self.request(url, method='DELETE', data={"items": items_to_delete})

            if not res_del.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='DELETE', error=res_del.get('errors')
                    )
                )

            op_id = res_del['result']['operation_id']
            self.wait_for_operation(op_id)

            for item in self.payload_put:
                self.payload_post.append({"redirect": item["redirect"]})

        if self.payload_post:
            info, res_post = self.request(url, method='POST', data=self.payload_post)

            if not res_post.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='POST', error=res_post.get('errors')
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

    def verify_credentials(self):
        """
        Verify API credentials and connection against Cloudflare API.
        """
        url = self.CF_API_ENDPOINTS['account'].format(account_id=self.account_id)
        info, response_json = self.request(url, method='GET')
        
        if not response_json.get('success'):
            self.module.fail_json(
                msg=error_messages['cf_api_error'].format(
                    action='VERIFY_CREDENTIALS', error=response_json.get('errors')
                )
            )
        return response_json

    def get_items_list(self):
        """
        Fetch existing items from the specified Cloudflare List using pagination.
        """
        existing_items = {}
        cursor = None
        per_page = 100

        while True:
            url = f"{self.CF_API_ENDPOINTS['list_items'].format(account_id=self.account_id, list_id=self.list_id)}?per_page={per_page}"
            if cursor:
                url += f"&cursor={cursor}"

            info, response_json = self.request(url, method='GET')

            if not response_json.get('success'):
                self.module.fail_json(
                    msg=error_messages['cf_api_error'].format(
                        action='GET_ITEMS', error=response_json.get('errors')
                    )
                )

            result = response_json.get('result', [])
            if not result:
                break

            for item in result:
                source = item['redirect']['source_url']
                item_id = item['id']
                existing_items[source] = item_id

            cursor = response_json.get('result_info', {}).get('cursors', {}).get('after')
            if not cursor:
                break

        return existing_items

    @staticmethod
    def is_home(url):
        """
        Validate if the given URL path corresponds to the home domain.
        """
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "//" + clean_url

        parsed = urlparse(clean_url)
        return parsed.path in ("", "/")

    @staticmethod
    def format_source_url(url):
        """
        Normalize source URL by stripping schema, query strings, and trailing hashes.
        """
        clean_url = url.strip()
        clean_url = re.sub(r'^https?://', '', clean_url, flags=re.IGNORECASE)

        if '/' in clean_url:
            domain, path = clean_url.split('/', 1)
            clean_url = f"{domain.lower()}/{path}"
        else:
            clean_url = clean_url.lower()

        clean_url = clean_url.split('?')[0].split('#')[0]
        return clean_url

    @staticmethod
    def format_target_url(url):
        """
        Ensure target URL always starts with explicit https:// schema.
        """
        clean_url = url.strip()

        if re.match(r'^https?://', clean_url, flags=re.IGNORECASE):
            clean_url = re.sub(r'^https?://', 'https://', clean_url, flags=re.IGNORECASE)
        else:
            clean_url = f"https://{clean_url}"

        return clean_url

    @staticmethod
    def parse_bool(value):
        """
        Safely convert string representations to boolean values.
        """
        if isinstance(value, bool):
            return value
        
        clean_val = str(value).strip().lower()
        return clean_val in ("true", "1", "yes", "y", "t")