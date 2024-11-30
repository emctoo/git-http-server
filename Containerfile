FROM docker.io/library/caddy:2.8.4-alpine

RUN apk add --no-cache git fcgiwrap spawn-fcgi

RUN adduser -D -h /git git \
    && mkdir -p /git/repos && chown -R git:git /git \
    && mkdir -p /run/fcgiwrap && chown git:git /run/fcgiwrap

COPY Caddyfile /etc/caddy/Caddyfile
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80
VOLUME ["/git/repos"]

USER git
ENTRYPOINT ["/start.sh"]
