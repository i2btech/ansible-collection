# I2B Ansible Collection

# Devcontainer

You need to build a docker image to run the devcontainer using this command:
```
docker buildx bake devcontainer
```

Then, you need to create a file to set environment variables, you need to update the values if you need to run some [tests](./tests/README.md)
```
cp .devcontainer/.env.sample .devcontainer/.env
```

Now you can start the devcontainer.

# Modules

- [Bitbucket](src/README.bitbucket.md)
- [Google Workspace](src/README.gws.md)

# Roles

- logrotate

# Playbooks

- [logrotate](src/README.playbooks.md#logrotate)
- [sqlbackup](src/README.playbooks.md#sqlbackup)

# Dockerhub

We can use a docker image to run the playbooks of the collection.

## Test

You need to build a docker image to test the execution of playbooks:
```
docker buildx bake playbooks
```

Then, you need to use docker compose to run the test(s):
```
# logrotate
docker compose -f test-playbooks.yml up logrotate

# sqlbackup
docker compose -f test-playbooks.yml up sqlbackup
```

## Build and release to Ansible Galaxy and Dockerhub from local

You need to have at hand the values for secrets `ANSIBLE_GALAXY_API_KEY` and `DOCKER_LOGIN_PASS`

```
./build_release_local.sh
```

# TODO

- set environment variable "TAG" with value equal to "steps.cversion.outputs.version" in release workflow
- Add [ansible-test](https://www.ansible.com/blog/introduction-to-ansible-test)

# Links

- https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general
