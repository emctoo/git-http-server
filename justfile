image := "git-http-server"
version := "0.1.0"
host_repo_dir := "${PWD}/repos"

_default:
    @just --list

build:
    podman image rm {{image}}:{{version}}
    podman build -t {{image}}:{{version}} .

run: build
    podman run -it --rm --name {{image}} -p 8080:80 -v $PWD/repos/:/git/repos -v $PWD/logs:/var/log:Z localhost/{{image}}:{{version}}

log file="log/caddy/access.log":
    #!/usr/bin/env bash
    set -x -euo pipefail

    tail -f {{file}} | jq -r '
        if .logger == "http.log.access" then
            "[\(.ts|todate)] Access: \(.request.method) \(.request.uri) -> \(.status)"
        elif .logger == "http.handlers.rewrite" then
            "[\(.ts|todate)] Rewrite: \(.request.uri) -> \(.uri)"
        elif .logger == "http.handlers.reverse_proxy" then
            if .msg == "selected upstream" then
                "[\(.ts|todate)] Proxy: Selected \(.dial)"
            elif .msg == "upstream roundtrip" then
                "[\(.ts|todate)] Proxy: \(.request.method) \(.request.uri) -> \(.status)"
            else
                "[\(.ts|todate)] Proxy: \(.msg)"
            end
        elif .logger == "http.reverse_proxy.transport.fastcgi" then
            "[\(.ts|todate)] FastCGI: \(.request.method) \(.request.uri)\nEnv:\n\(.env | to_entries | map("  \(.key) = \(.value)") | .[])"
        else
            "[\(.ts|todate)] \(.logger): \(.msg)"
        end'
