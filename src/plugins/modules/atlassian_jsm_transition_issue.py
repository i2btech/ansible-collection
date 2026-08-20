#!/usr/bin/python
# -*- coding: utf-8 -*-
""" atlassian_jsm_transition_issue module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: atlassian_jsm_transition_issue
short_description: Transition a Jira Service Management Cloud issue after an automated task
version_added: "1.0.0"
description:
    - Transition a Jira Service Management (JSM) Cloud issue after the execution of an automated task,
      and add a comment describing the outcome.
    - When O(issue_resolution) is provided, the issue is transitioned to a successful/closed state, the
      resolution is set, and O(comment) is added as a public comment (visible to the customer).
    - When O(issue_assignee) is provided, the issue is transitioned to a state requesting human attention,
      it is reassigned to the given agent, and O(comment) is added as a private/internal note.
options:
    jira_username:
        description:
            - Email address of the Atlassian account used for authentication.
        type: str
        required: true
    jira_password:
        description:
            - API token associated with O(jira_username), used for authentication.
        type: str
        required: true
    issue_url:
        description:
            - Full browse URL of the issue to transition, e.g. C(https://i2btech.atlassian.net/browse/I2B-113).
        type: str
        required: true
    issue_status:
        description:
            - Name or ID of the transition/status the issue should be moved to.
        type: str
        required: true
    comment:
        description:
            - Text of the comment to add to the issue.
            - Added as a public (customer-visible) comment when O(issue_resolution) is set, or as a
              private/internal note when O(issue_assignee) is set.
        type: str
        required: true
    issue_assignee:
        description:
            - Email of the human agent the issue should be assigned to.
            - Required when the associated task finished with an error. Mutually exclusive with O(issue_resolution).
        type: str
        required: false
    issue_resolution:
        description:
            - Resolution to set on the issue as part of the transition.
            - Required when the associated task finished successfully. Mutually exclusive with O(issue_assignee).
        type: str
        required: false
    validate_certs:
        description:
            - Whether to validate SSL certificates when contacting the Jira/JSM Cloud API.
        type: bool
        default: true
    use_proxy:
        description:
            - Whether to use the configured proxy when contacting the Jira/JSM Cloud API.
        type: bool
        default: true
    force_basic_auth:
        description:
            - Whether to force basic authentication headers on every request.
        type: bool
        default: true
    return_content:
        description:
            - Whether to return the body content of the response.
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
    - Exactly one of O(issue_assignee) or O(issue_resolution) must be provided.
    - In check mode, no API call is made and the module always reports C(changed=false).
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Close issue after successful automated task"
  i2btech.ops.atlassian_jsm_transition_issue:
    jira_username: "{{ jira_user }}"
    jira_password: "{{ jira_pass }}"
    issue_url: "https://i2btech.atlassian.net/browse/I2B-113"
    issue_status: "Completado"
    comment: "Requerimiento completado"
    issue_resolution: "Done"

- name: "Send issue back to a human agent after automated task failure"
  i2btech.ops.atlassian_jsm_transition_issue:
    jira_username: "{{ jira_user }}"
    jira_password: "{{ jira_pass }}"
    issue_url: "https://i2btech.atlassian.net/browse/I2B-113"
    issue_status: "Trabajo en curso"
    comment: "Se produjo el siguiente error: xxx"
    issue_assignee: "alvaro.chandia@i2btech.com"
'''

RETURN = r'''
changed:
    description: Whether the issue was transitioned.
    type: bool
    returned: always
issue_key:
    description: The Jira issue key parsed from issue_url.
    type: str
    returned: always
    sample: I2B-113
transition:
    description: The id and name of the transition that was applied.
    type: dict
    returned: always
resolution:
    description: The resolution that was set on the issue.
    type: str
    returned: when issue_resolution is provided
assignee:
    description: The accountId the issue was assigned to.
    type: str
    returned: when issue_assignee is provided
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.atlassian_jsm import AtlassianJsmHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position

def run_module():
    """ main module """

    # define available arguments/parameters a user can pass to the module

    module_args = AtlassianJsmHelper.atlassian_jsm_argument_spec()
    module_args.update(
        issue_url=dict(
            type='str',
            required=True,
            no_log=False),
        issue_status=dict(
            type='str',
            required=True,
            no_log=False),
        comment=dict(
            type='str',
            required=True,
            no_log=False),
        issue_assignee=dict(
            type='str',
            required=False,
            no_log=False,
            default=None),
        issue_resolution=dict(
            type='str',
            required=False,
            no_log=False,
            default=None),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        issue_key=None,
        transition={},
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[('issue_assignee', 'issue_resolution')],
        required_one_of=[('issue_assignee', 'issue_resolution')],
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    jsm = AtlassianJsmHelper(module)
    is_success_path = module.params['issue_resolution'] is not None

    transition = jsm.resolve_transition(module.params['issue_status'])

    if is_success_path:
        jsm.transition_issue(transition['id'], resolution=module.params['issue_resolution'])
    else:
        jsm.transition_issue(transition['id'])
        account_id = jsm.find_account_id(module.params['issue_assignee'])
        jsm.assign_issue(account_id)

    jsm.add_comment(module.params['comment'], public=is_success_path)

    result['changed'] = True
    result['issue_key'] = jsm.issue_key
    result['transition'] = {'id': transition['id'], 'name': transition.get('name')}
    if is_success_path:
        result['resolution'] = module.params['issue_resolution']
    else:
        result['assignee'] = account_id

    module.exit_json(**result)

def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()
