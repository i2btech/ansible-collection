# Testing

This folder allow us to simulate a live environment where the collection will be installed and use the sample playbooks to test the execution of the modules

## Bitbucket

You need to create an [APP Password](https://support.atlassian.com/bitbucket-cloud/docs/create-an-app-password/) to interact with the Bitbucket API, the following permissions are needed:

| Repositories  | Pipelines     |
| ------------- |:-------------:|
| Read          | Read          |
| Write         | Write         |
| Admin         | Edit variables|
| Delete        |               |

To execute the modules run one of the following commands:

```
ansible-playbook bitbucket-repo.yml
ansible-playbook bitbucket-repo-perm.yml
ansible-playbook bitbucket-repo-var.yml
ansible-playbook bitbucket-repo-env.yml
```