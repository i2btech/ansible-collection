# Bitbucket

## Caveats about API

- Status of task that use modules `bitbucket_repo_var` or `bitbucket_repo_env` will always be changed if you include some secure variable. This happens because the API will never expose the value of secure variables, this is stated on the [documentation](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pipelines/#api-repositories-workspace-repo-slug-pipelines-config-variables-variable-uuid-get) of the response of the endpoint, because of this, we always need to update this kind of variables
- To change the type of a variables from `secure` to `unsecured` and viceversa you need to delete an re-create the variable
- Currently, at 2023-01-13, the [endpoint](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-deployments/#api-repositories-workspace-repo-slug-environments-environment-uuid-changes-post) to update the name of a deployment environment doesn't work, if need to change the name you need to delete manually the environment and re-create it
- Pagination over the list of variables of a repository or deployment environment is not working, the URL included in the variable "next" of the response deliver an error. We apply a workaround similar to [this](https://jira.atlassian.com/browse/BCLOUD-13806) to fix the error

## TODO

- Adds validation to check if parameter `project_key` exists on `bitbucket_repo` modulue, if not, module need to fail.

## Links

- https://github.com/juanenriqueescobar/bitbucket, example of test and strategy to better handle secured vars
- https://github.com/NordeaOSS/esp.bitbucket, base code for the collection
