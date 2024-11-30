#!/bin/sh

mkdir -p /var/log/caddy
chown -R git:git /var/log/caddy

spawn-fcgi -s /run/fcgiwrap/socket -u git -g git -P /run/fcgiwrap/fcgiwrap.pid -- /usr/bin/fcgiwrap -f 2> /var/log/fcgiwrap.log &


# Start caddy with debug output
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
