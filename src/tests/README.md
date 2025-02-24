# Testing

This folder allow us to simulate a live environment where the collection will be installed and use the sample playbooks to test the execution of the modules

## Bitbucket

### Credential

You need to create an [APP Password](https://support.atlassian.com/bitbucket-cloud/docs/create-an-app-password/) to interact with the Bitbucket API, the following permissions are needed:

| Repositories  | Pipelines     |
| ------------- |:-------------:|
| Read          | Read          |
| Write         | Write         |
| Admin         | Edit variables|
| Delete        |               |

To execute the modules run one of the following commands:

### Commands

```
ansible-playbook bitbucket-repo.yml
ansible-playbook bitbucket-repo-perm.yml
ansible-playbook bitbucket-repo-var.yml
ansible-playbook bitbucket-repo-env.yml
```

## Google Workspace

### Credential

Follow [this steps](https://stackoverflow.com/a/72022166) to configure authentication, you need to put the `credential.json` in the same folder where the playbook is located.

### Commands

To execute the modules run one of the following commands:

```
ansible-playbook gws-user-management.yml -t signature
ansible-playbook gws-user-management.yml -t signout
ansible-playbook gws-user-management.yml -t create_update
ansible-playbook gws-group-management.yml -t check
ansible-playbook gws-group-management.yml -t create_update
```
