---
description: "A deployable MCP server is an ordinary containerized HTTP service — the only MCP-specific pieces are the health check and making sure logs never touch stdout on the stdio path."
---

# 09 · Deploying a Remote MCP Server

A Streamable HTTP MCP server is, underneath the protocol, just an HTTP
service. Deploying it looks almost exactly like deploying any other backend
— container it, put TLS in front of it, configure it with environment
variables, give it a health check.

## A Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["python", "http_server.py"]
```

```text
# requirements.txt
mcp[cli]
httpx
```

Make sure `http_server.py` reads the port from the environment instead of
hardcoding it, so the same image works regardless of what port the hosting
platform assigns:

```python
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github-tools")
# ... tools from Lesson 7 ...

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=int(os.environ.get("PORT", 8000)))
```

```bash
docker build -t github-mcp-server .
docker run -p 8000:8000 -e GITHUB_TOKEN=ghp_xxx github-mcp-server
```

## TLS and a reverse proxy

Don't terminate TLS inside the Python process. Put a reverse proxy (nginx,
Caddy, or your cloud provider's load balancer) in front of the container,
handling HTTPS termination and forwarding plain HTTP to the container on
its internal port:

```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;

    ssl_certificate     /etc/letsencrypt/live/mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.example.com/privkey.pem;

    location /mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;  # required for SSE streaming to pass through
    }
}
```

`proxy_buffering off` matters specifically because of the SSE stream from
Lesson 2 — a buffering proxy will hold onto server-sent events instead of
forwarding them immediately, breaking anything that depends on timely
delivery.

## A health check endpoint

Hosting platforms and load balancers need something to poll that doesn't
require a full MCP session:

```python
from starlette.responses import PlainTextResponse

@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request):
    return PlainTextResponse("ok")
```

Point your platform's health check (or the load balancer's) at `/healthz`,
not at `/mcp` — the MCP endpoint expects real protocol traffic, not a bare
`GET` with no session.

## A basic production checklist

- **Environment-variable configuration** for every secret (API tokens, auth
  issuer URLs) — never baked into the image.
- **Structured logging to stderr or a logging service**, never to stdout —
  the stdout-corruption rule from Level 1 only applies to stdio transport,
  but it's a cheap habit to keep everywhere so the same server code works
  on either transport without a silent trap.
- **A health check endpoint**, as above, so the platform can tell a crashed
  container from a healthy one.
- **Graceful shutdown** — handle `SIGTERM` by finishing in-flight requests
  before exiting, so a deploy or scale-down doesn't cut off an active tool
  call mid-response.
- **Rate limiting at the proxy layer**, in addition to anything your own
  code does (like Lesson 7's GitHub rate-limit check), as a backstop against
  a misbehaving or malicious client hammering the endpoint directly.

## Exercise

Add `SIGTERM` handling to `http_server.py`: on receiving the signal, log
"shutting down" to stderr, stop accepting new connections, and exit cleanly
once any in-flight request finishes (or after a 10-second timeout,
whichever comes first). Test it by starting the server, sending a `SIGTERM`
with `docker stop`, and confirming your log line appears before the
container actually exits.
