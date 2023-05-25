# Ansible Collection - i2btech.bitbucket

## Development

Install the dependencies and virtual environment for the collection executing this commands:
```
python -m venv ansi-venv
source ansi-venv/bin/activate
pip install -r requirements.txt
```

Create a playbook to test the modules using one of the samples located on the root:
```
cp sample-pb-XX.yml pb-XX.yml
```

To execute the modules run one of the following commands:
```
ansible-playbook pb-repo.yml
ansible-playbook pb-repo-perm.yml
ansible-playbook pb-repo-var.yml
ansible-playbook pb-repo-env.yml
```

We need pass as parameter an [APP Password](https://support.atlassian.com/bitbucket-cloud/docs/create-an-app-password/) to interact with the Bitbucket API, the following permissions are needed:

| Repositories  | Pipelines     |
| ------------- |:-------------:|
| Read          | Read          |
| Write         | Write         |
| Admin         | Edit variables|
| Delete        |               |

## Caveats about Bitbucket API

- Status of task that use modules `repo_var` or `repo_env` will always be changed if you include some secure variable. This happens because the API will never expose the value of secure variables, this is stated on the [documentation](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pipelines/#api-repositories-workspace-repo-slug-pipelines-config-variables-variable-uuid-get) of the response of the endpoint, because of this, we always need to update this kind of variables
- To change the type of a variables from `secure` to `unsecured` and viceversa you need to delete an re-create the variable
- Currently, at 2023-01-13, the [endpoint](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-deployments/#api-repositories-workspace-repo-slug-environments-environment-uuid-changes-post) to update the name of a deployment environment doesn't work, if need to change the name you need to delete manually the environment and re-create it
- Pagination over the list of variables of a repository or deployment environment is not working, the URL included in the variable "next" of the response deliver an error. We apply a workaround similar to [this](https://jira.atlassian.com/browse/BCLOUD-13806) to fix the error

## TODO

- Adds validation to check if parameter `project_key` exists on `repo` modulue, if not, module need to fail.
- Add [ansible-test](https://www.ansible.com/blog/introduction-to-ansible-test)

## Links

- https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general
- https://github.com/juanenriqueescobar/bitbucket, example of test and strategy to better handle secured vars
- https://github.com/NordeaOSS/esp.bitbucket, base code for the collection
