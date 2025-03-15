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
```

# TODO

- Add [ansible-test](https://www.ansible.com/blog/introduction-to-ansible-test)

# Links

- https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general
