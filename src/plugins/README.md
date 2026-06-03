# Collections Plugins Directory

This directory can be used to ship various plugins inside an Ansible collection. Each plugin is placed in a folder that
is named after the type of plugin it is in. It can also include the `module_utils` and `modules` directory that
would contain module utils and modules respectively.

Here is an example directory of the majority of plugins currently supported by Ansible:

```
└── plugins
    ├── action
    ├── become
    ├── cache
    ├── callback
    ├── cliconf
    ├── connection
    ├── filter
    ├── httpapi
    ├── inventory
    ├── lookup
    ├── module_utils
    ├── modules
    ├── netconf
    ├── shell
    ├── strategy
    ├── terminal
    ├── test
    └── vars
```

A full list of plugin types can be found at [Working With Plugins](https://docs.ansible.com/ansible-core/2.13/plugins/plugins.html).

# Bitbucket

- [API documentation](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-branch-restrictions/#api-group-branch-restrictions)
- [API Definition](https://dac-static.atlassian.com/cloud/bitbucket/swagger.v3.json)
- API v1 for group management
    - https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/
    - https://support.atlassian.com/bitbucket-cloud/docs/group-privileges-endpoint/

# Ansible

- [Developing modules](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general)
