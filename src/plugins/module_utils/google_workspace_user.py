"""
Util class for google_workspace_user
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account
from jinja2 import Environment, FileSystemLoader
from googleapiclient import errors
from ansible_collections.i2btech.ops.plugins.module_utils.google_workspace_group import GoogleWorkspaceGroupHelper
import time

#
# class: GoogleWorkspaceUserHelper
#

class GoogleWorkspaceUserHelper:
    """
    Class GoogleWorkspaceUserHelper
    """

    def __init__(self, module):
        self.module = module


    def signout(self):

        result_signout = {
            "changed": False,
            "failed": False,
            "message": []
        }

        users_from_groups = []
        target_scopes = ["https://www.googleapis.com/auth/admin.directory.group.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes)
        service_members = build("admin", "directory_v1", credentials=credentials)

        if self.module.params['groups'] is not None:
            for group in self.module.params['groups']:
                users_from_groups = GoogleWorkspaceGroupHelper.get_members(self, group, service_members)

        target_scopes_security = ["https://www.googleapis.com/auth/admin.directory.user.security"]
        credentials_security = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes_security,
            subject=self.module.params['used_by'])
        service_signout = build("admin", "directory_v1", credentials=credentials_security)

        if (len(self.module.params['users']) == 0) and len(users_from_groups) == 0:
            result_signout['failed'] = True
            result_signout['message'].append("Need users or groups")
        else:
            for user in self.module.params['users'] + users_from_groups:
                try:
                    results = (
                        service_signout.users()
                        .signOut(userKey=user)
                        .execute()
                    )
                    result_signout['changed'] = True
                except Exception as error:
                    result_signout['failed'] = True
                    current_user = {
                        "user": user,
                        "message": error
                    }
                    result_signout['message'].append(current_user)

        if not result_signout['failed']:
            result_signout['message'].append("All sessions closed")

        return result_signout


    def render_signature(self, user_info, template_folder):
        # create signature from template
        env = Environment(loader=FileSystemLoader(template_folder))
        rendered_string = env.get_template(user_info['signature'] + ".j2").render(
            full_name=user_info['full_name'],
            title=user_info['title'],
            phone=user_info['phone'] if "phone" in user_info else None,
            calendar=user_info['calendar'] if "calendar" in user_info else None,
            time_zone=user_info['time_zone'] if "time_zone" in user_info else None,
        )
        return rendered_string


    def set_signature(self):

        result_signature = {
            "changed": False,
            "failed": False,
            "message": []
        }

        # get users from current groups
        users_from_groups = []
        for group in self.module.params['groups_definition']:
            if group['mail'] in self.module.params['groups']:
                users_from_groups = users_from_groups + group['members']

        if (len(self.module.params['users']) == 0) and len(users_from_groups) == 0:
            result_signature['failed'] = True
            result_signature['message'].append("Need users or groups")
        else:
            # iterate over list of all users that need to be updated
            for user in self.module.params['users'] + users_from_groups:
                try:
                    # iterate over list of all current users if use that need to be updated
                    # exist, apply change
                    for current_user in self.module.params['users_definition']:
                        if current_user['mail'] == user:

                            # auth google
                            target_scopes = ["https://www.googleapis.com/auth/gmail.settings.basic"]
                            credentials = service_account.Credentials.from_service_account_file(
                                self.module.params['credential_file'],
                                scopes=target_scopes,
                                subject=current_user['mail'])
                            service_user = build("gmail", "v1", credentials=credentials)

                            send_as_configuration = {
                                "signature": self.render_signature(current_user, self.module.params['signature_folder']),
                            }
                            # pylint: disable=E1101
                            result = (
                                service_user.users()
                                .settings()
                                .sendAs()
                                .patch(
                                    userId=current_user['mail'],
                                    sendAsEmail=current_user['mail'],
                                    body=send_as_configuration,
                                )
                                .execute()
                            )
                            result_signature['changed'] = True

                except Exception as error:
                    result_signature['failed'] = True
                    current_user = {
                        "user": user,
                        "message": error
                    }
                    result_signature['message'].append(current_user)

        if not result_signature['failed']:
            result_signature['message'].append("Signatures updated")

        return result_signature

    def create_update(self):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }

        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.user",
            "https://www.googleapis.com/auth/admin.directory.group.member",
            "https://www.googleapis.com/auth/admin.directory.group"
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes,
            subject=self.module.params['used_by'])
        service_directory = build("admin", "directory_v1", credentials=credentials)

        # get list of users that need to be created/updated
        action_users = self.module.params['users'] if "users" in self.module.params else []
        for user in action_users:

            # get detail of user from list
            user_definition = next((sub for sub in self.module.params['users_definition'] if sub['mail'] == user), None)
            if user_definition is None:
                result["failed"] = True
                result["message"] = "User definition don't exist"
                break

            # get list of groups to define to which ones the user need to be added
            groups_definition = self.module.params['groups_definition'] if "groups_definition" in self.module.params else []
            groups_to_be_added = []
            for group in groups_definition:
                members_list = group['members'] if "members" in group else []
                if user in members_list:
                   groups_to_be_added.append(group["mail"])

            IF_EXIST_RES=self.check_if_exists(service_directory, user)
            if IF_EXIST_RES == "TRUE":
                result = self.update(service_directory, user_definition, groups_to_be_added)
            elif IF_EXIST_RES == "FALSE":
                result = self.create(service_directory, user_definition, groups_to_be_added)
            else:
                result["failed"] = True
                result["message"] = IF_EXIST_RES

        return result

    def check_if_exists(self, service, user):
        result = "NONE"
        try:
            results = (
                service.users()
                .get(userKey=user)
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


    def create(self, service_directory, user, groups):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            body_info = {
                "primaryEmail": user["mail"],
                "password": user["password"],
                "changePasswordAtNextLogin": "false",
                "name": {
                    "fullName": user["full_name"],
                    "familyName": user["last_name"],
                    "givenName": user["first_name"],
                    "displayName": user["full_name"]
                }
            }
            service_directory.users().insert(body=body_info).execute()
            result["changed"] = True

            # TODO: existe opcion archived en body de usuario (Indicates if user is archived.)
            # será igual q el grupo?, se crea en modo archived y hay q esperar la activación?
            time.sleep(5)

            # add to groups
            for group in groups:
                res = GoogleWorkspaceGroupHelper.member_insert_delete(self, "insert", service_directory, group, user["mail"])
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(user["mail"] + ": " + res)
                else:
                    result["changed"] = True

        except Exception as error:
            result['failed'] = True
            result["message"] = error

        return result


    def update(self, service_directory, user, groups_to_be_added):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            body_info = {
                "primaryEmail": user["mail"],
                "changePasswordAtNextLogin": "false",
                "name": {
                    "fullName": user["full_name"],
                    "familyName": user["last_name"],
                    "givenName": user["first_name"],
                    "displayName": user["full_name"]
                }
            }
            res = service_directory.users().update(
                userKey=user["mail"],
                body=body_info
                ).execute()
            # TODO: need to validate if options where actually changed
            result["changed"] = True

            # get current memberships
            current_memberships = []
            results = (
                service_directory.groups()
                .list(userKey=user["mail"])
                .execute()
            )
            if "groups" in results:
                for group in results["groups"]:
                    current_memberships.append(group["email"])

            # delete memberships
            for deleted in set(current_memberships).difference(groups_to_be_added):
                res = GoogleWorkspaceGroupHelper.member_insert_delete(self, "delete", service_directory, deleted, user["mail"])
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(deleted + ": " + res)
                else:
                    result["changed"] = True

            # add memberships
            for added in set(groups_to_be_added).difference(current_memberships):
                res = GoogleWorkspaceGroupHelper.member_insert_delete(self, "insert", service_directory, added, user["mail"])
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(added + ": " + res)
                else:
                    result["changed"] = True

        except Exception as error:
            result["failed"] = True
            result["message"].append(str(error))

        return result
