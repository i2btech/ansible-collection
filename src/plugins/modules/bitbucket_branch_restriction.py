#!/usr/bin/python
# -*- coding: utf-8 -*-
""" bitbucket_branch_restriction module """

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: bitbucket_branch_restriction
short_description: Manage branch restriction rules for a repository on Bitbucket Cloud
version_added: "1.0.0"
description:
    - Manage branch restriction rules for a repository on Bitbucket Cloud.
    - Supports creating, updating, and deleting branch restriction rules.
    - A rule is uniquely identified by its C(kind) combined with its match definition
      (C(branch_match_kind) + C(pattern) for glob, or C(branch_match_kind) + C(branch_type)
      for branching model).
options:
    username:
        description:
            - Username used for authentication.
        type: str
        required: true
    password:
        description:
            - Password used for authentication.
        type: str
        required: true
    repository:
        description:
            - Repository slug (name).
        type: str
        required: true
    restrictions:
        description:
            - List of branch restriction rules to enforce on the repository.
            - Rules not present in this list that currently exist on the repository will be deleted.
        type: list
        elements: dict
        required: true
        suboptions:
            kind:
                type: str
                description:
                    - The type of restriction to apply.
                choices:
                    - push
                    - force
                    - delete
                    - restrict_merges
                    - require_tasks_to_be_completed
                    - require_approvals_to_merge
                    - require_default_reviewer_approvals_to_merge
                    - require_no_changes_requested
                    - require_passing_builds_to_merge
                    - require_commits_behind
                    - reset_pullrequest_approvals_on_change
                    - smart_reset_pullrequest_approvals
                    - reset_pullrequest_changes_requested_on_change
                    - require_all_dependencies_merged
                    - enforce_merge_checks
                    - allow_auto_merge_when_builds_pass
                required: true
            branch_match_kind:
                type: str
                description:
                    - How to match the branch. Use C(glob) to match by pattern, or
                      C(branching_model) to match by branch type.
                choices:
                    - glob
                    - branching_model
                required: true
            pattern:
                type: str
                description:
                    - Glob pattern to match branches against.
                    - Required when C(branch_match_kind) is C(glob).
                    - C('*') matches any branch.
                required: false
            branch_type:
                type: str
                description:
                    - The branch type from the repository branching model to match.
                    - Required when C(branch_match_kind) is C(branching_model).
                choices:
                    - production
                    - development
                    - bugfix
                    - release
                    - feature
                    - hotfix
                required: false
            value:
                type: int
                description:
                    - Numeric value for restrictions that require a count, such as
                      C(require_approvals_to_merge) or C(require_commits_behind).
                required: false
            users:
                type: list
                elements: str
                description:
                    - List of user account IDs (UUIDs) exempted from the restriction.
                    - Only applicable for C(push) and C(restrict_merges) kinds.
                required: false
                default: []
            groups:
                type: list
                elements: str
                description:
                    - List of group slugs exempted from the restriction.
                    - Only applicable for C(push) and C(restrict_merges) kinds.
                required: false
                default: []
author:
    - IT I2B (it@i2btech.com)
'''

EXAMPLES = r'''
- name: "Configure branch restrictions for repository X"
  i2btech.ops.bitbucket_branch_restriction:
    username: "alice"
    password: "app_password"
    repository: "example-X"
    restrictions:
      - kind: push
        branch_match_kind: glob
        pattern: main
        users: []
        groups:
          - administrators
      - kind: force
        branch_match_kind: glob
        pattern: "main"
      - kind: require_approvals_to_merge
        branch_match_kind: branching_model
        branch_type: production
        value: 2
      - kind: delete
        branch_match_kind: glob
        pattern: "*"
'''

RETURN = r'''
message:
    description: Placeholder for return value
    type: dict
    returned: always
    sample: []
'''

#pylint: disable=wrong-import-position
from ansible_collections.i2btech.ops.plugins.module_utils.bitbucket import BitbucketHelper
from ansible.module_utils.basic import AnsibleModule
#pylint: disable=wrong-import-position


def _restriction_key(restriction):
    """
    Return a tuple that uniquely identifies a branch restriction rule.
    The combination of kind + branch_match_kind + (pattern or branch_type) must be unique per repo.
    """
    kind = restriction.get('kind', '')
    branch_match_kind = restriction.get('branch_match_kind', '')
    if branch_match_kind == 'glob':
        return (kind, branch_match_kind, restriction.get('pattern', ''))
    return (kind, branch_match_kind, restriction.get('branch_type', ''))


def _restriction_payload(restriction):
    """
    Build the API payload dict from an Ansible task restriction dict.
    """
    payload = {
        'type': 'branchrestriction',
        'kind': restriction['kind'],
        'branch_match_kind': restriction['branch_match_kind'],
    }
    if restriction['branch_match_kind'] == 'glob':
        payload['pattern'] = restriction.get('pattern', '')
    else:
        payload['branch_type'] = restriction.get('branch_type', '')

    if restriction.get('value') is not None:
        payload['value'] = restriction['value']

    users = restriction.get('users') or []
    payload['users'] = [{'type': 'account', 'uuid': uid} for uid in users]

    groups = restriction.get('groups') or []
    payload['groups'] = [{'type': 'group', 'slug': slug} for slug in groups]

    return payload


def _restrictions_differ(desired, current):
    """
    Return True if the desired restriction differs from the current one
    and therefore needs to be updated via PUT.
    """
    # Compare value
    desired_value = desired.get('value')
    current_value = current.get('value')
    if desired_value != current_value:
        return True

    # Compare users by UUID
    desired_users = sorted(desired.get('users') or [])
    current_users = sorted(
        u.get('uuid', u.get('account_id', ''))
        for u in (current.get('users') or [])
    )
    if desired_users != current_users:
        return True

    # Compare groups by slug
    desired_groups = sorted(desired.get('groups') or [])
    current_groups = sorted(
        g.get('slug', '')
        for g in (current.get('groups') or [])
    )
    if desired_groups != current_groups:
        return True

    return False


def manage_restrictions(result, bitbucket, module):
    """ CRUD branch restrictions """

    current_restrictions = bitbucket.get_branch_restrictions()
    # Build a lookup map: key -> current restriction object
    current_map = {_restriction_key(r): r for r in current_restrictions}

    desired_restrictions = module.params['restrictions'] or []
    desired_keys = set()

    for desired in desired_restrictions:
        key = _restriction_key(desired)
        desired_keys.add(key)

        payload = _restriction_payload(desired)

        if key in current_map:
            current = current_map[key]
            if _restrictions_differ(desired, current):
                bitbucket.manage_branch_restriction(
                    action='update',
                    restriction_data=payload,
                    restriction_id=current['id'],
                )
                result['changed'] = True
        else:
            bitbucket.manage_branch_restriction(
                action='create',
                restriction_data=payload,
            )
            result['changed'] = True

    # Delete restrictions no longer in the desired list
    for key, current in current_map.items():
        if key not in desired_keys:
            bitbucket.manage_branch_restriction(
                action='delete',
                restriction_id=current['id'],
            )
            result['changed'] = True


def run_module():
    """ main module """

    restriction_spec = dict(
        kind=dict(
            required=True,
            type='str',
            choices=[
                'push',
                'force',
                'delete',
                'restrict_merges',
                'require_tasks_to_be_completed',
                'require_approvals_to_merge',
                'require_default_reviewer_approvals_to_merge',
                'require_no_changes_requested',
                'require_passing_builds_to_merge',
                'require_commits_behind',
                'reset_pullrequest_approvals_on_change',
                'smart_reset_pullrequest_approvals',
                'reset_pullrequest_changes_requested_on_change',
                'require_all_dependencies_merged',
                'enforce_merge_checks',
                'allow_auto_merge_when_builds_pass',
            ],
        ),
        branch_match_kind=dict(
            required=True,
            type='str',
            choices=['glob', 'branching_model'],
        ),
        pattern=dict(
            required=False,
            type='str',
            default=None,
        ),
        branch_type=dict(
            required=False,
            type='str',
            choices=['production', 'development', 'bugfix', 'release', 'feature', 'hotfix'],
            default=None,
        ),
        value=dict(
            required=False,
            type='int',
            default=None,
        ),
        users=dict(
            required=False,
            type='list',
            elements='str',
            default=[],
        ),
        groups=dict(
            required=False,
            type='list',
            elements='str',
            default=[],
        ),
    )

    module_args = BitbucketHelper.bitbucket_argument_spec()
    module_args.update(
        repository=dict(
            type='str',
            required=True,
            no_log=False,
            aliases=['name'],
        ),
        restrictions=dict(
            type='list',
            elements='dict',
            required=True,
            no_log=False,
            options=restriction_spec,
        ),
    )

    result = dict(
        changed=False,
        message=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if module.check_mode:
        module.exit_json(**result)

    bitbucket = BitbucketHelper(module)

    existing_repository = bitbucket.get_repository_info()

    if existing_repository:
        manage_restrictions(result, bitbucket, module)
    else:
        module.fail_json(msg="Repository doesn't exist")

    module.exit_json(**result)


def main():
    """ main function """

    run_module()


if __name__ == '__main__':
    main()
