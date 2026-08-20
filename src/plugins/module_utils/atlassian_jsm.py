"""
Util class for atlassian_jsm_transition_issue
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re
import time
from urllib.parse import urlencode
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import fetch_url, basic_auth_header

#
# class: AtlassianJsmHelper
#

error_messages = {
    'invalid_issue_url': 'Unable to parse `issue_url` ({issue_url}), expected a URL like https://<site>.atlassian.net/browse/<ISSUE-KEY>',
    'transition_not_found': 'No transition matching `{issue_status}` was found for issue `{issue_key}`. Available transitions: {available}',
    'assignee_not_found': 'No Jira user found matching email `{issue_assignee}`',
    'assignee_ambiguous': 'More than one Jira user matched email `{issue_assignee}`, cannot determine accountId unambiguously',
    'unknown_error': 'An unknown error happened `{info}',
}

class AtlassianJsmHelper:
    """
    Class AtlassianJsmHelper
    """

    JSM_API_ENDPOINTS = {
        'transitions': '{base_url}/rest/api/3/issue/{issue_key}/transitions',
        'assignee': '{base_url}/rest/api/3/issue/{issue_key}/assignee',
        'user-search': '{base_url}/rest/api/3/user/search',
        'comment': '{base_url}/rest/servicedeskapi/request/{issue_key}/comment',
    }

    def __init__(self, module):
        self.module = module
        self.base_url, self.issue_key = self.parse_issue_url(module.params['issue_url'])

        if not self.base_url or not self.issue_key:
            module.fail_json(
                msg=error_messages['invalid_issue_url'].format(
                    issue_url=module.params['issue_url'],
                )
            )

    @staticmethod
    def parse_issue_url(issue_url):
        """
        Parse a Jira browse URL like https://i2btech.atlassian.net/browse/I2B-113
        into (base_url, issue_key).
        """

        match = re.match(r'^(https?://[^/]+)/browse/([A-Za-z][A-Za-z0-9_]*-[0-9]+)/?$', issue_url or '')
        if not match:
            return None, None
        return match.group(1), match.group(2)

    @staticmethod
    def atlassian_jsm_argument_spec():
        """
        Define default arguments for modules
        """

        return dict(
            jira_username=dict(
                type='str',
                required=True,
                no_log=False),
            jira_password=dict(
                type='str',
                required=True,
                no_log=True),
            validate_certs=dict(
                type='bool',
                default=True),
            use_proxy=dict(
                type='bool',
                default=True),
            force_basic_auth=dict(
                type='bool',
                default=True),
            return_content=dict(
                type='bool',
                default=True),
            sleep=dict(
                type='int',
                default=5),
            retries=dict(
                type='int',
                default=3),
        )

    def request(
        self,
        api_url,
        method,
        data=None,
        headers=None):
        """
        Function to interact with the Jira/JSM Cloud REST API
        """

        headers = headers or {}

        headers.update({
            'Authorization': basic_auth_header(
                self.module.params['jira_username'],
                self.module.params['jira_password']
            )
        })

        if isinstance(data, dict):
            data = self.module.jsonify(data)
            if 'Content-type' not in headers:
                headers.update({
                    'Content-type': 'application/json',
                })

        retries = 1
        while retries <= self.module.params['retries']:
            response, info = fetch_url(
                module=self.module,
                url=api_url,
                method=method,
                headers=headers,
                data=data,
                force=True,
                use_proxy=self.module.params['use_proxy']
            )
            if (info is not None) and (info['status'] != -1):
                break
            time.sleep(self.module.params['sleep'])
            retries += 1

        content = {}

        if response is not None:

            body = to_text(response.read())
            if body:
                try:
                    body_js = json.loads(body)
                    if isinstance(body_js, dict):
                        content = body_js
                    else:
                        content['json'] = body_js
                except ValueError:
                    content['content'] = body

        content['fetch_url_retries'] = retries

        return info, content

    def get_transitions(self):
        """
        Retrieve the list of available transitions for the issue.
        """

        info, content = self.request(
            api_url=self.JSM_API_ENDPOINTS['transitions'].format(
                base_url=self.base_url,
                issue_key=self.issue_key,
            ),
            method='GET',
        )

        if info['status'] == 200:
            return content.get('transitions', [])

        self.module.fail_json(
            msg=error_messages['unknown_error'].format(
                info=info,
            )
        )

        return None

    def resolve_transition(self, issue_status):
        """
        Resolve issue_status (name or id) to a transition dict.
        Matches against the transition id, transition name, or destination
        status id/name (case-insensitive).
        """

        transitions = self.get_transitions()
        wanted = str(issue_status).strip().lower()

        for transition in transitions:
            candidates = [
                str(transition.get('id', '')).lower(),
                str(transition.get('name', '')).lower(),
                str(transition.get('to', {}).get('id', '')).lower(),
                str(transition.get('to', {}).get('name', '')).lower(),
            ]
            if wanted in candidates:
                return transition

        available = ', '.join(
            '{0} (id={1}, to={2})'.format(
                t.get('name'), t.get('id'), t.get('to', {}).get('name')
            ) for t in transitions
        )

        self.module.fail_json(
            msg=error_messages['transition_not_found'].format(
                issue_status=issue_status,
                issue_key=self.issue_key,
                available=available or 'none',
            )
        )

        return None

    def transition_issue(self, transition_id, resolution=None):
        """
        Perform the issue transition. If resolution is given, it is set
        on the transition screen fields.
        """

        data = {'transition': {'id': transition_id}}
        if resolution:
            data['fields'] = {'resolution': {'name': resolution}}

        info, content = self.request(
            api_url=self.JSM_API_ENDPOINTS['transitions'].format(
                base_url=self.base_url,
                issue_key=self.issue_key,
            ),
            method='POST',
            data=data,
        )

        if info['status'] == 204:
            return True

        self.module.fail_json(
            msg=error_messages['unknown_error'].format(
                info=info,
            )
        )

        return None

    def find_account_id(self, email):
        """
        Resolve an email address to a Jira accountId via the user search API.
        """

        api_url = self.JSM_API_ENDPOINTS['user-search'].format(
            base_url=self.base_url,
        ) + '?' + urlencode({'query': email})

        info, content = self.request(
            api_url=api_url,
            method='GET',
        )

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        users = content.get('json', []) if isinstance(content.get('json'), list) else []
        exact_matches = [u for u in users if u.get('active', False)]

        if len(exact_matches) == 0:
            self.module.fail_json(
                msg=error_messages['assignee_not_found'].format(
                    issue_assignee=email,
                )
                # msg=content.get('json', [])
            )

        if len(exact_matches) > 1:
            self.module.fail_json(
                msg=error_messages['assignee_ambiguous'].format(
                    issue_assignee=email,
                )
            )

        return exact_matches[0]['accountId']

    def assign_issue(self, account_id):
        """
        Assign the issue to the given accountId.
        """

        info, content = self.request(
            api_url=self.JSM_API_ENDPOINTS['assignee'].format(
                base_url=self.base_url,
                issue_key=self.issue_key,
            ),
            method='PUT',
            data={'accountId': account_id},
        )

        if info['status'] == 204:
            return True

        self.module.fail_json(
            msg=error_messages['unknown_error'].format(
                info=info,
            )
        )

        return None

    def add_comment(self, comment, public):
        """
        Add a comment to the JSM request. public=True makes it visible to
        the customer, public=False adds it as an internal note.
        """

        info, content = self.request(
            api_url=self.JSM_API_ENDPOINTS['comment'].format(
                base_url=self.base_url,
                issue_key=self.issue_key,
            ),
            method='POST',
            data={'body': comment, 'public': public},
        )

        if info['status'] in (200, 201):
            return content

        self.module.fail_json(
            msg=error_messages['unknown_error'].format(
                info=info,
            )
        )

        return None
