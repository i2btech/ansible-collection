# I2B Ansible Collection

# Devcontainer

You need to build a docker image to run the devcontainer using this command:
```
docker build -f .devcontainer/Dockerfile --tag i2btech/ansible-collection .
```

Then, you need to create a file to set environment variables, you need to update the values if you need to run some [tests](./tests/README.md)
```
cp .devcontainer/.env.sample .devcontainer/.env
```

Now you can start the devcontainer.

# Modules

- [Bitbucket](src/README.bitbucket.md)
- [Google Workspace](src/README.gws.md)

# TODO

- Add [ansible-test](https://www.ansible.com/blog/introduction-to-ansible-test)

# Links

- https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#developing-modules-general
