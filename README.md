# Ansible Collection - i2btech.bitbucket

## Development

Install the dependencies and virtual environment for the collection executing this commands:
```
pip install -r requirements.txt
source ansi-venv/bin/activate
```

Create an args.json file using one of the sample located on the root:
```
cp args-sample_repo.json args_repo.json
```

To execute the module run one of the following commands:
```
python plugins/modules/repo.py args_repo.json
python plugins/modules/repo_perm.py args_perm.json
python plugins/modules/repo_var.py args_var.json
python plugins/modules/repo_env.py args_env.json
```

## TODO

- module `repo`: Adds validation to check if parameter `project_key` exists, if not, module need to fail.

## Links

- https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general
