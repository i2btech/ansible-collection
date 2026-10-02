"""
Util class for google_workspace_groups_check
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account

#
# class: GoogleWorkspaceGroupCheckHelper
#

class GoogleWorkspaceGroupCheckHelper:
    """
    Class GoogleWorkspaceGroupCheckHelper
    """

    def __init__(self, module):
        self.module = module

    def get_all_group_members(self, service, group_email):
        members_list = []
        page_token = None

        while True:
            response = service.members().list(
                groupKey=group_email,
                pageToken=page_token,
                maxResults=200
            ).execute()

            for member in response.get("members", []):
                if "email" in member:
                    members_list.append(member["email"].lower())

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return set(members_list)

    def check_membership(self):
        result = {
            "changed": False,
            "failed": False,
            "missing_users": [],
            "unexpected_users": [],
            "in_group_count": 0,
            "expected_count": 0,
            "msg": ""
        }

        try:
            target_scopes = ["https://www.googleapis.com/auth/admin.directory.group.readonly"]
            credentials = service_account.Credentials.from_service_account_file(
                self.module.params['credential_file'],
                scopes=target_scopes
            )
            service = build("admin", "directory_v1", credentials=credentials)

            group_email = self.module.params['group_email'].lower().strip()
            expected_users = set(u.lower().strip() for u in self.module.params['expected_users'])
            excluded_users = set(u.lower().strip() for u in self.module.params.get('excluded_users', []))

            target_users = expected_users - excluded_users

            actual_members = self.get_all_group_members(service, group_email)

            missing = sorted(list(target_users - actual_members))
            unexpected = sorted(list(actual_members - target_users))

            result["missing_users"] = missing
            result["unexpected_users"] = unexpected
            result["in_group_count"] = len(actual_members)
            result["expected_count"] = len(target_users)

            if missing or unexpected:
                result["failed"] = True
                result["msg"] = f"El grupo {group_email} presenta discrepancias de membresia."
            else:
                result["msg"] = f"Todos los usuarios requeridos estan presentes en {group_email}."

        except Exception as error:
            result["failed"] = True
            result["msg"] = f"Error al verificar la membresia: {repr(error)}"

        return result