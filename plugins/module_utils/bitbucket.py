"""
Util class for bitbucket_repo
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import time
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url, basic_auth_header

#
# class: BitbucketHelper
#

error_messages = {
    'insufficient_permissions_to_see': 'The currently authenticated user has insufficient permissions to see `{repositorySlug}` repository',
    'repository_does_not_exist': '`{repositorySlug}` repository does not exist',
    'validation_error': '`{repositorySlug}` repository was not created due to a validation error',
    'repository_already_exists': 'A repository with same name ({repositorySlug}) already exists',
    'insufficient_permissions_to_delete': 'The currently authenticated user has insufficient permissions to delete `{repositorySlug}` repository',
    'insufficient_permissions_to_create': 'The currently authenticated user has insufficient permissions to create `{repositorySlug}` repository',
    'unknown_error': 'An unknown error happened `{info}',
}

class BitbucketHelper:
    """
    Class BitbucketHelper
    """

    BITBUCKET_API_URL = 'https://api.bitbucket.org/2.0'

    BITBUCKET_API_ENDPOINTS = {
        'repos': '{url}/repositories/{workspace}/{repo_slug}',
        'repos-permissions-users': '{url}/repositories/{workspace}/{repo_slug}/permissions-config/users',
        'repos-permissions-groups': '{url}/repositories/{workspace}/{repo_slug}/permissions-config/groups',
        'repos-pipeline': '{url}/repositories/{workspace}/{repo_slug}/pipelines_config',
        'repos-environments': '{url}/repositories/{workspace}/{repo_slug}/environments',
        'repos-deployments': '{url}/repositories/{workspace}/{repo_slug}/deployments_config',
    }

    def __init__(self, module):
        self.module = module
        if self.module.params['url'] is None:
            self.module.params['url'] = self.BITBUCKET_API_URL

    @staticmethod
    def bitbucket_argument_spec():
        """
        Define default arguments for modules
        """

        return dict(
            url=dict(
                type='str',
                no_log=False,
                required=False),
            username=dict(
                type='str',
                no_log=False,
                required=False,
                default=None,
                aliases=['user'],
                fallback=(env_fallback, ['BITBUCKET_USER_ID'])),
            password=dict(
                type='str',
                no_log=True,
                required=False,
                default=None),
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
        module,
        method,
        data=None,
        headers=None):
        """
        Function to interact with Bitbucket API
        """

        headers = headers or {}

        if module.params['username']:
            headers.update({
                'Authorization': basic_auth_header(module.params['username'], module.params['password'])
            })

        if isinstance(data, dict):
            data = module.jsonify(data)
            if 'Content-type' not in headers:
                headers.update({
                    'Content-type': 'application/json',
                })

        retries = 1
        while retries <= module.params['retries']:
            response, info = fetch_url(
                module=module,
                url=api_url,
                method=method,
                headers=headers,
                data=data,
                force=True,
                use_proxy=module.params['use_proxy']
            )
            if (info is not None) and (info['status'] != -1):
                break
            time.sleep(module.params['sleep'])
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
                except ValueError as exc:
                    content['content'] = body

        content['fetch_url_retries'] = retries

        return info, content

    def get_repository_info(self):
        """
        Get information of repository on Bitbucket
        """

        info, content = self.request(
            api_url=self.BITBUCKET_API_ENDPOINTS['repos'].format(
                url=self.BITBUCKET_API_URL,
                workspace='i2b',
                repo_slug=self.module.params['repository']
            ),
            module=self.module,
            method='GET',
        )

        if info['status'] == 200:
            return content

        if info['status'] == 404:
            return False

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def create_repository(self):
        """
        Create a bitbucket repository
        """

        info, content = self.request(
            api_url=self.BITBUCKET_API_ENDPOINTS['repos'].format(
                url=self.BITBUCKET_API_URL,
                workspace='i2b',
                repo_slug=self.module.params['repository']
            ),
            module=self.module,
            method='POST',
            data={
                'project': ({
                    'key': self.module.params['project_key'],
                }),
                'is_private': True
            },
        )

        if info['status'] == 200:
            return True

        if info['status'] == 400:
            self.module.fail_json(
                msg=error_messages['insufficient_permissions_to_create'].format(
                    repositorySlug=self.module.params['repository'],
                )
            )

        if info['status'] == 401:
            self.module.fail_json(
                msg=error_messages['validation_error'].format(
                    repositorySlug=self.module.params['repository'],
                )
            )

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def get_repository_permissions_info(
        self,
        scope=None):
        """
        Retrieve users or groups that have been granted at least one permission for the specified repository.
        scope: either 'users' or 'groups'.
        """

        permissions = []
        is_last_page = False
        api_url=None

        if scope == "user":
            api_url=self.BITBUCKET_API_ENDPOINTS['repos-permissions-users'].format(
                        url=self.module.params['url'],
                        workspace='i2b',
                        repo_slug=self.module.params['repository'])
        else:
            api_url=self.BITBUCKET_API_ENDPOINTS['repos-permissions-groups'].format(
                        url=self.module.params['url'],
                        workspace='i2b',
                        repo_slug=self.module.params['repository'])

        while not is_last_page:
            info, content = self.request(
                api_url,
                module=self.module,
                method='GET',
            )

            for value in content['values']:
                perm = {}
                if scope == "user":
                    perm =	{
                        "type": scope,
                        "name": value['user']['nickname'],
                        "perm": value['permission']
                    }
                else:
                    perm =	{
                        "type": scope,
                        "name": value['group']['slug'],
                        "perm": value['permission']
                    }

                permissions.extend([perm])

            if 'next' in content:
                api_url = content['next']
            else:
                is_last_page = True

        if info['status'] == 200:
            return permissions

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def apply_repository_permissions(
        self,
        action,
        scope,
        name,
        perm=None):
        """
        Promote or demote either a user's or a group's permission level for the specified repository
        scope: either 'user' or 'group'.
        """

        if scope == "group":
            api_url=self.BITBUCKET_API_ENDPOINTS['repos-permissions-groups'].format(
                        url=self.module.params['url'],
                        workspace='i2b',
                        repo_slug=self.module.params['repository'])

        if action == "promote":
            api_verb = 'PUT'
            api_data={
                'permission': perm
            }
        elif action == "demote":
            api_verb = 'DELETE'
            api_data = {}

        info, content = self.request(
            api_url + '/' + name,
            module=self.module,
            method=api_verb,
            data=api_data
        )

        if info['status'] == 200 or info['status'] == 204:
            return content

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def enable_repository_pipeline(
        self,
        ):
        """
        Enable pipeline on repository
        """

        api_url=self.BITBUCKET_API_ENDPOINTS['repos-pipeline'].format(
            url=self.BITBUCKET_API_URL,
            workspace='i2b',
            repo_slug=self.module.params['repository']
        )

        info, content = self.request(
            api_url,
            module=self.module,
            method='PUT',
            data={
                'enabled': True
            },
        )

        if info['status'] == 200:
            return content

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def get_variables(
        self,
        api_url):
        """
        Retrieve all variables for the specified repository.
        """

        variables = []
        is_last_page = False
        current_page = 1
        current_size = 0
        while not is_last_page:
            info, content = self.request(
                api_url,
                module=self.module,
                method='GET',
            )

            if 'values' in content:
                variables.extend(content['values'])

            if 'next' in content:
                current_page = sum([current_page, 1])
                api_url = api_url + "?page=" + str(current_page)

            current_size = sum([current_size, content['pagelen']])
            if current_size >= content['size']:
                is_last_page = True

            # this is the logic we need to use to paginate over the response
            # but the URL included in the "next" option is currently not working
            # if 'next' in content:
            #     api_url = content['next']
            # else:
            #     is_last_page = True

        if info['status'] == 200:
            return variables

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def manage_repository_variables(
        self,
        action,
        name,
        value,
        uuid=None,
        secured=False):
        """
        CRUD variables on repository
        """

        api_url=self.BITBUCKET_API_ENDPOINTS['repos-pipeline'].format(
                    url=self.module.params['url'],
                    workspace='i2b',
                    repo_slug=self.module.params['repository'])

        if action == "create":
            api_verb = 'POST'
            api_data={
                'key': name,
                'value': value,
                'secured': secured
            }
            api_path="/variables/"
        elif action == "update":
            api_verb = 'PUT'
            api_data={
                'key': name,
                'value': value,
                'secured': secured,
                'uuid': uuid
            }
            api_path="/variables/" + uuid
        elif action == "delete":
            api_verb = 'DELETE'
            api_data={}
            api_path="/variables/" + uuid

        info, content = self.request(
            api_url + api_path,
            module=self.module,
            method=api_verb,
            data=api_data
        )

        if info['status'] == 200:
            return content

        if info['status'] == 201 and action == "create":
            return content

        if info['status'] == 204 and action == "delete":
            return content

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        # error 409: A variable with the provided key already exists.

        return None

    def get_repository_environments(
        self):
        """
        Retrieve all environments for the specified repository.
        """

        variables = []
        is_last_page = False

        api_url=self.BITBUCKET_API_ENDPOINTS['repos-environments'].format(
                    url=self.module.params['url'],
                    workspace='i2b',
                    repo_slug=self.module.params['repository'])

        while not is_last_page:
            info, content = self.request(
                api_url + "/",
                module=self.module,
                method='GET',
            )

            if 'values' in content:
                variables.extend(content['values'])

            if 'next' in content:
                api_url = content['next']
            else:
                is_last_page = True

        if info['status'] == 200:
            return variables

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def manage_repository_environments(
        self,
        action,
        name,
        category=None,
        uuid=None):
        """
        CRUD environments on repository
        """

        api_url=self.BITBUCKET_API_ENDPOINTS['repos-environments'].format(
                    url=self.module.params['url'],
                    workspace='i2b',
                    repo_slug=self.module.params['repository'])

        if action == "create":
            api_verb = 'POST'
            api_data={
                'name': name,
                'type': 'deployment_environment_type',
                "environment_type":{
                    "type": "deployment_environment_type",
                    "name": category
                },
            }
            api_path="/"
        elif action == "delete":
            api_verb = 'DELETE'
            api_data={}
            api_path="/" + uuid

        info, content = self.request(
            api_url + api_path,
            module=self.module,
            method=api_verb,
            data=api_data
        )

        if info['status'] == 201 and action == "create":
            return content
        elif info['status'] == 204 and action == "delete":
            return content
        else:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        return None

    def manage_environment_variables(
        self,
        action,
        name,
        value,
        env_uuid=None,
        var_uuid=None,
        secured=False):
        """
        CRUD variables on environment
        """

        api_url=self.BITBUCKET_API_ENDPOINTS['repos-deployments'].format(
                    url=self.module.params['url'],
                    workspace='i2b',
                    repo_slug=self.module.params['repository'])

        if action == "create":
            api_verb = 'POST'
            api_data={
                'key': name,
                'value': value,
                'secured': secured
            }
            api_path="/environments/" + env_uuid + "/variables"
        elif action == "update":
            api_verb = 'PUT'
            api_data={
                'key': name,
                'value': value,
                'secured': secured,
                'uuid': var_uuid
            }
            api_path="/environments/" + env_uuid + "/variables/" + var_uuid
        elif action == "delete":
            api_verb = 'DELETE'
            api_data={}
            api_path="/environments/" + env_uuid + "/variables/" + var_uuid

        info, content = self.request(
            api_url + api_path,
            module=self.module,
            method=api_verb,
            data=api_data
        )

        if info['status'] == 200:
            return content

        if info['status'] == 201 and action == "create":
            return content

        if info['status'] == 204 and action == "delete":
            return content

        if info['status'] != 200:
            self.module.fail_json(
                msg=error_messages['unknown_error'].format(
                    info=info,
                )
            )

        # error 409: A variable with the provided key already exists.

        return None
