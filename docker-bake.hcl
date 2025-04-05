variable "TAG" {
  default = "latest"
}

group "devcontainer" {
  targets = ["base", "devcontainer"]
}

group "playbooks" {
  targets = ["base", "playbooks"]
}

target "base" {
  dockerfile = ".devcontainer/Dockerfile.base"
  tags = ["i2btech/ansible-collection:base"]
}

target "devcontainer" {
  dockerfile = ".devcontainer/Dockerfile.devcontainer"
  tags = ["i2btech/ansible-collection:devcontainer"]
  contexts = {
    ansible-collection-base = "target:base"
  }
}

target "playbooks" {
  dockerfile = ".devcontainer/Dockerfile.playbooks"
  tags = ["i2btech/ansible-collection:${TAG}"]
  contexts = {
    ansible-collection-base = "target:base"
  }
}
