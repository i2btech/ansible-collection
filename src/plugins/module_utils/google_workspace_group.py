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


    def parse_email_list(self, value):
        if not value:
            return []
        return [email.strip() for email in value.split(",") if email.strip()]


    def get_members(self, group, service):

        results = (
            service.members()
            .list(groupKey=group)
            .execute()
        )
        members = results.get("members", [])
        user_list = []
        if len(members) > 0:
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
            settings_definition.update({"allowExternalMembers": group_definition.get("allow_externals", "false")})
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
            scopes=target_scopes)
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

        # self managed group (smg) membership params - apply only to groups
        # whose definition has an "admins" key
        admin_requester = self.module.params.get('smg_admin_requester')
        members_add = self.parse_email_list(self.module.params.get('smg_members_add'))
        members_remove = self.parse_email_list(self.module.params.get('smg_members_remove'))
        smg_params_provided = bool(admin_requester or members_add or members_remove)

        smg_targets = []
        for group in action_groups:
            group_definition = next((sub for sub in self.module.params['groups_definition'] if sub['mail'] == group), None)
            if group_definition is not None and "admins" in group_definition:
                smg_targets.append(group)

        if smg_params_provided and len(smg_targets) > 1:
            result["failed"] = True
            result["message"] = (
                "smg_admin_requester/smg_members_add/smg_members_remove were provided but "
                f"{len(smg_targets)} self-managed groups are targeted in 'groups' ({smg_targets}); "
                "invoke this module once per self-managed group when managing membership"
            )
            return result

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

            is_smg = "admins" in group_definition
            skip_membership_sync = False

            if is_smg:
                if not admin_requester:
                    # no requester passed this run - leave membership untouched,
                    # settings/name/description still get synced below
                    skip_membership_sync = True
                elif admin_requester not in group_definition.get("admins", []):
                    result["failed"] = True
                    result["message"] = (
                        f"'{admin_requester}' is not authorized to manage group "
                        f"'{group_definition['mail']}' (not present in its 'admins' list)"
                    )
                    break

            IF_EXIST_RES=self.check_if_exists(service_directory, group, self.module.params['customer_id'])
            if IF_EXIST_RES == "TRUE":
                result = self.update(service_directory, group_definition, type_definition, service_grp_settings)
            elif IF_EXIST_RES == "FALSE":
                result = self.create(service_directory, group_definition, type_definition, service_grp_settings)
            else:
                result["failed"] = True
                result["message"] = IF_EXIST_RES
                break

            if is_smg and not skip_membership_sync and not result["failed"]:
                smg_result = self.smg_sync_members(service_directory, group_definition["mail"], members_add, members_remove)
                result["changed"] = result["changed"] or smg_result["changed"]
                result["failed"] = result["failed"] or smg_result["failed"]
                result["message"] = result["message"] + smg_result["message"]

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
                type["settings"][0].update({"allowExternalMembers": group.get("allow_externals", "false")})
                service_grp_settings.groups().patch(
                    groupUniqueId=group["mail"],
                    body=type["settings"][0]
                ).execute()

                # add users - self managed groups (admins present) start with no
                # static membership; smg_members_add is applied afterwards by
                # create_update() via smg_sync_members()
                definition_members = [] if "admins" in group else group.get("members", [])
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
            result["message"].append(f"Details: {repr(error)}")

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
            type["settings"][0].update({"allowExternalMembers": group.get("allow_externals", "false")})

            service_grp_settings.groups().patch(
                groupUniqueId=group["mail"],
                body=type["settings"][0]
            ).execute()
            # TODO: need to validate if settings where actually changed
            result["changed"] = True

            # self managed groups (admins present) never reconcile membership
            # against a static "members" list - membership is handled at
            # runtime by create_update() via smg_sync_members()
            if "admins" not in group:
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
            result["message"].append(f"Details: {repr(error)}")

        return result


    def smg_sync_members(self, service_directory, group_mail, members_add, members_remove):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            current_members = []
            results = (
                service_directory.members()
                .list(groupKey=group_mail)
                .execute()
            )
            if "members" in results:
                for member in results["members"]:
                    current_members.append(member["email"])

            current_set = set(current_members)
            remove_set = set(members_remove)
            # if an email is in both lists, removal wins
            add_set = set(members_add) - remove_set

            for member in sorted(remove_set & current_set):
                res = self.member_insert_delete("delete", service_directory, group_mail, member)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(member + ": " + res)
                else:
                    result["changed"] = True

            for member in sorted(add_set - current_set):
                res = self.member_insert_delete("insert", service_directory, group_mail, member)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(member + ": " + res)
                else:
                    result["changed"] = True

        except Exception as error:
            result["failed"] = True
            result["message"].append(f"Details: {repr(error)}")

        return result


    def check_if_exists(self, service, group, customer_id):
        result = "NONE"
        try:
            results = service.groups().list(
                customer=customer_id,
                query=f"email={group}",
                maxResults=1,
            ).execute()
            groups = results.get("groups", [])
            return ("TRUE") if groups else ("FALSE")
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
