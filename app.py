import os
import subprocess
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("git-http-server")

GIT_HTTP_BACKEND = os.getenv(
    "GIT_HTTP_BACKEND", "/usr/libexec/git-core/git-http-backend"
)
GIT_ROOT = os.getenv("GIT_PROJECT_ROOT", "/git/repos")


def parse_request(environ):
    return {
        "path": environ.get("PATH_INFO", ""),
        "method": environ.get("REQUEST_METHOD"),
        "query_string": environ.get("QUERY_STRING", ""),
        "content_type": environ.get("CONTENT_TYPE", ""),
        "content_length": environ.get("CONTENT_LENGTH", ""),
        "body": environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0) or 0)),
    }


def setup_git_env(request):
    return {
        "GIT_PROJECT_ROOT": GIT_ROOT,
        "GIT_HTTP_EXPORT_ALL": "true",
        "REMOTE_USER": "git",
        "PATH_INFO": request["path"],
        "QUERY_STRING": request["query_string"],
        "REQUEST_METHOD": request["method"],
        "CONTENT_TYPE": request["content_type"],
        "CONTENT_LENGTH": request["content_length"],
    }


def execute_git_backend(git_env, body):
    logger.debug(f"Starting git-http-backend with env: {git_env}")
    process = subprocess.Popen(
        [GIT_HTTP_BACKEND],
        env=git_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate(input=body)

    if stderr:
        logger.warning(f"git-http-backend stderr: {stderr.decode('utf-8')}")

    return stdout, stderr, process.returncode


def parse_response(stdout):
    status = "200 OK"
    response_headers = []

    if b"\r\n\r\n" in stdout:
        headers_raw, body = stdout.split(b"\r\n\r\n", 1)
        headers = headers_raw.decode("utf-8")
    else:
        headers = ""
        body = stdout

    for line in headers.split("\n"):
        if not line.strip():
            continue
        if line.lower().startswith("status:"):
            status = line.split(":", 1)[1].strip()
        else:
            key, value = line.split(":", 1)
            response_headers.append((key.strip(), value.strip()))

    if not any(h[0].lower() == "content-type" for h in response_headers):
        response_headers.append(("Content-Type", "application/octet-stream"))

    return status, response_headers, body


def application(environ, start_response):
    try:
        request = parse_request(environ)
        logger.info(f"Received {request['method']} request for {request['path']}")

        git_env = setup_git_env(request)
        stdout, stderr, returncode = execute_git_backend(git_env, request["body"])

        if returncode != 0:
            logger.error(f"git-http-backend failed with code {returncode}")
            start_response(
                "500 Internal Server Error", [("Content-Type", "text/plain")]
            )
            return [stderr]

        status, headers, body = parse_response(stdout)
        logger.info(f"Responding with status {status}")

        start_response(status, headers)
        return [body]

    except Exception as e:
        logger.exception("Error handling git request")
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [str(e).encode()]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    logger.info("Starting git-http-server ...")
    logger.info(f"GIT_HTTP_BACKEND: {GIT_HTTP_BACKEND}")
    logger.info(f"GIT_ROOT: {GIT_ROOT}")

    httpd = make_server("0.0.0.0", 8000, application)
    httpd.serve_forever()

