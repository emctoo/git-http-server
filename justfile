image := "git-http-server"
version := "0.1.0"
host_repo_dir := "${PWD}/repos"

_default:
    @just --list

build:
    podman build -t {{image}}:{{version}} .

run: build
    podman run -d --rm --name {{image}} -p 8000:8000 --userns=keep-id -v /tmp/repos:/git/repos localhost/{{image}}:{{version}}

