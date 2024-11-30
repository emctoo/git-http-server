FROM docker.io/library/python:3.12-alpine

RUN apk add --no-cache git-daemon
RUN adduser -D -h /git git && mkdir -p /git/repos && chown -R git:git /git
COPY app.py /user/local/bin/app.py

EXPOSE 8000
VOLUME ["/git/repos"]

USER git
CMD ["python", "/user/local/bin/app.py"]
