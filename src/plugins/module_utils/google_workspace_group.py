"""
Util class for google_workspace_groups
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient import errors
import time

#
# class: GoogleWorkspaceGroupHelper
#

class GoogleWorkspaceGroupHelper:
    """
    Class GoogleWorkspaceGroupHelper
    """

    def __init__(self, module):
        self.module = module


    def get_members(self, group, service):

        results = (
            service.members()
            .list(groupKey=group)
            .execute()
        )
        members = results.get("members", [])
        user_list = []
        if len(members) > 1:
            for member in members:
                user_list.append(member['email'])

        return user_list


    def check_config(self):

        result = {
            "changed": False,
            "failed": False,
            "message": []
        }

        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.group.readonly",
            "https://www.googleapis.com/auth/apps.groups.settings",
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes)
        service = build("groupssettings", "v1", credentials=credentials)

        # check if special keyword exists
        # in this case we check all the groups
        action_groups = self.module.params['groups'] if "groups" in self.module.params else []
        if "ALL" in action_groups:
            action_groups = []
            all_groups_definition = self.module.params['groups_definition'] if "groups_definition" in self.module.params else []
            for group in all_groups_definition:
                action_groups.append(group["mail"])

        for group in action_groups:
            group_definition = next((sub for sub in self.module.params['groups_definition'] if sub['mail'] == group), None)
            if group_definition is None:
                result["failed"] = True
                result["message"] = "Group definition don't exist "
                return result

            types_definition = next((sub for sub in self.module.params['groups_types'] if sub['name'] == group_definition["type"]), None)
            if types_definition is None:
                result["failed"] = True
                result["message"] = "Group type definition don't exist "
                return result

            settings_definition = types_definition["settings"][0]
            settings_current = self.get_settings(service, group)

            if settings_definition != settings_current:
                result["failed"] = True
                settings = {
                    "group": group,
                    "status": "NOT_MATCH",
                    "current": settings_current,
                    "definition": settings_definition
                }
                result["message"].append(settings)
            else:
                settings = {
                    "group": group,
                    "status": "MATCH"
                }
                result["message"].append(settings)

        return result


    def get_settings(self, service, group):

        results_group_settings = (
            service.groups()
            .get(groupUniqueId=group)
            .execute()
        )

        current_settings = {}
        current_settings["whoCanJoin"] = results_group_settings['whoCanJoin']
        current_settings["whoCanAdd"] = results_group_settings['whoCanAdd']
        current_settings["whoCanInvite"] = results_group_settings['whoCanInvite']
        current_settings["whoCanViewMembership"] = results_group_settings['whoCanViewMembership']
        current_settings["allowExternalMembers"] = results_group_settings['allowExternalMembers']
        current_settings["whoCanContactOwner"] = results_group_settings['whoCanContactOwner']
        current_settings["whoCanViewGroup"] = results_group_settings['whoCanViewGroup']
        current_settings["whoCanPostMessage"] = results_group_settings['whoCanPostMessage']

        return current_settings


    def create_update(self):

        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.group",
            "https://www.googleapis.com/auth/admin.directory.group.member"
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes,
            subject=self.module.params['used_by'])
        service_directory = build("admin", "directory_v1", credentials=credentials)

        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.group",
            "https://www.googleapis.com/auth/apps.groups.settings",
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes)
        service_grp_settings = build("groupssettings", "v1", credentials=credentials)

        # get list of group that need to be created/updated
        action_groups = self.module.params['groups'] if "groups" in self.module.params else []
        for group in action_groups:

            # get detail of group from list
            group_definition = next((sub for sub in self.module.params['groups_definition'] if sub['mail'] == group), None)
            if group_definition is None:
                result["failed"] = True
                result["message"] = "Group definition don't exist"
                break

            # get detail of group type
            type_definition = next((sub for sub in self.module.params['groups_types'] if sub['name'] == group_definition["type"]), None)
            if type_definition is None:
                result["failed"] = True
                result["message"] = "Type definition don't exist"
                break

            IF_EXIST_RES=self.check_if_exists(service_directory, group)
            if IF_EXIST_RES == "TRUE":
                result = self.update(service_directory, group_definition, type_definition, service_grp_settings)
            elif IF_EXIST_RES == "FALSE":
                result = self.create(service_directory, group_definition, type_definition, service_grp_settings)
            else:
                result["failed"] = True
                result["message"] = IF_EXIST_RES

        return result
 

    def create(self, service_directory, group, type, service_grp_settings):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            body_info = {
                "email": group["mail"],
                "name": group["name"],
                "description": group["description"]
            }
            service_directory.groups().insert(body=body_info).execute()
            result["changed"] = True

            # wait for group to be active after creation
            for i in range(0,6):
                time.sleep(5)
                results_new_group_settings = (
                    service_grp_settings.groups()
                    .get(groupUniqueId=group["mail"])
                    .execute()
                )
                if results_new_group_settings["archiveOnly"] == "false":
                    GROUP_ACTIVE = True
                    break
                else:
                    GROUP_ACTIVE = False

            if GROUP_ACTIVE:
                # apply settings
                service_grp_settings.groups().patch(
                    groupUniqueId=group["mail"],
                    body=type["settings"][0]
                ).execute()

                # add users
                definition_members = group["members"] if "members" in group else []
                for user in definition_members:
                    res = self.member_insert_delete("insert", service_directory, group["mail"], user)
                    if res != "OK":
                        result["failed"] = True
                        result["message"].append(user + ": " + res)
            else:
                result['failed'] = True
                result["message"].append(group["mail"] + ": group created but was not activated")

        except Exception as error:
            result['failed'] = True
            result["message"] = error

        return result


    def update(self, service_directory, group, type, service_grp_settings):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            # update name, description and settings
            type["settings"][0]["name"] = group["name"]
            type["settings"][0]["description"] = group["description"]

            service_grp_settings.groups().patch(
                groupUniqueId=group["mail"],
                body=type["settings"][0]
            ).execute()
            # TODO: need to validate if settings where actually changed
            result["changed"] = True

            # get defined members
            definition_members = group["members"] if "members" in group else []

            # get current members
            current_members = []
            results = (
                service_directory.members()
                .list(groupKey=group["mail"])
                .execute()
            )
            if "members" in results:
                for member in results["members"]:
                    current_members.append(member["email"])

            # add members
            for deleted in set(current_members).difference(definition_members):
                res = self.member_insert_delete("delete", service_directory, group["mail"], deleted)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(deleted + ": " + res)
                else:
                    result["changed"] = True

            # delete members
            for added in set(definition_members).difference(current_members):
                res = self.member_insert_delete("insert", service_directory, group["mail"], added)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(added + ": " + res)
                else:
                    result["changed"] = True

        except Exception as error:
            result["failed"] = True
            result["message"].append(str(error))

        return result


    def check_if_exists(self, service, group):
        result = "NONE"
        try:
            results = (
                service.groups()
                .get(groupKey=group)
                .execute()
            )
            result = "TRUE"
        except errors.HttpError as error:
            if str(error.status_code) == "404":
                result = "FALSE"
            else:
                result = str(error.error_details)
        except Exception as error:
            result = str(error)

        return result


    def member_insert_delete(self, action, service, group, member):
        result = "ERROR"
        try:
            if action == "insert":
                # TODO: insert method don't fail if the user don't exists
                body_member = {
                    "email": member
                }
                service.members().insert(
                    groupKey=group,
                    body=body_member
                ).execute()
                result = "OK"
            if action == "delete":
                service.members().delete(
                        groupKey=group,
                        memberKey=member
                    ).execute()
                result = "OK"

        except Exception as error:
            result = str(error)

        return result
