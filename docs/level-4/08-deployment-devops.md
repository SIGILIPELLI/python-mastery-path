# 08 · Deployment & DevOps

Writing an application is only part of the job — it needs to run reliably
somewhere other than your laptop. This module covers containerizing a Python
app with Docker, automating tests and builds with CI/CD, and managing
environment-specific configuration safely.

## Why containers

A container packages your application together with its exact runtime
environment (Python version, system libraries, dependencies), so "works on my
machine" becomes "works everywhere this image runs."

## A `Dockerfile` for a FastAPI app

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# copy only requirements first, so Docker can cache this layer
# and skip reinstalling dependencies when only app code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Building and running the image

```bash
docker build -t book-api:latest .
docker run -p 8000:8000 book-api:latest

# pass environment variables into the container
docker run -p 8000:8000 -e DATABASE_URL="sqlite:///./books.db" book-api:latest
```

## `.dockerignore`

Keep the build context small and avoid leaking local artifacts into the image.

```text
.venv/
__pycache__/
*.pyc
.git/
.pytest_cache/
tests/
```

## `docker-compose` for multi-service apps

Real applications usually need more than one container — the app plus a
database, for instance.

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://appuser:apppass@db:5432/appdb
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=apppass
      - POSTGRES_DB=appdb
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

```bash
docker compose up --build
docker compose down
```

Inside the compose network, the API reaches the database at hostname `db` —
Docker Compose sets up internal DNS between services automatically.

## Environment-based configuration

Never hard-code environment-specific values (database URLs, secrets, debug
flags) — read them from the environment so the same image behaves correctly
across dev, staging, and production.

```python
# config.py
import os

class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    secret_key: str = os.environ["SECRET_KEY"]   # required — fail fast if missing


settings = Settings()
```

Using `pydantic-settings` gives you validation and type coercion on top of
this pattern:

```bash
pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    debug: bool = False
    secret_key: str

    class Config:
        env_file = ".env"   # also loads from a local .env file, useful in development


settings = Settings()
```

## `.env` files (never commit real secrets)

```text
# .env  (local development only — add this file to .gitignore)
DATABASE_URL=postgresql://appuser:apppass@localhost:5432/appdb
DEBUG=true
SECRET_KEY=dev-only-secret-do-not-use-in-prod
```

```text
# .gitignore
.env
```

## CI/CD pipeline: test, build, push

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app

  build-and-push:
    needs: test               # only runs if tests passed
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: myorg/book-api:latest
```

Gating `build-and-push` behind `needs: test` means a broken build never gets
published as a deployable image — a fundamental CI/CD safety property.

## A minimal deployment checklist

| Concern | Practice |
|---------|----------|
| Reproducible environment | Dockerfile pinned to a specific Python base image |
| Secrets | environment variables / secret managers, never in source or images |
| Config differences (dev/stage/prod) | environment variables, not code branches |
| Automated verification | CI runs the full test suite on every push |
| Rollback safety | tag images by commit SHA, not just `latest` |
| Observability | structured logging (tying back to
[Production-Grade APIs](04-production-apis.md)'s middleware) |

## How It Actually Works

A Docker image is a stack of **read-only layers**, each one a filesystem diff from
the layer below it — every `FROM`, `COPY`, and `RUN` instruction in a Dockerfile
produces exactly one new layer, identified by a content hash of its resulting
filesystem changes. When you rebuild, Docker checks whether a given instruction's
inputs (its command text, and for `COPY`, the hash of the files being copied) match
a previously built layer with that same hash — if so, it reuses the cached layer
instead of re-executing the instruction. This is the entire mechanism behind the
"copy requirements.txt first" trick: as long as `requirements.txt` hasn't changed,
the `RUN pip install` layer's cache key matches and Docker skips reinstalling
everything, even though the `COPY app/` step after it (which changes on every code
edit) always misses cache and reruns — ordering instructions from least-to-most
frequently changing is what maximizes how much of the stack stays cached.

`docker run -p 8000:8000` sets up a **network address translation (NAT) rule** on
the host: the container gets its own isolated network namespace (its own virtual
network interface, its own view of `localhost`) via Linux kernel namespaces, and the
port mapping tells the host's networking stack to forward incoming connections on
host port 8000 to the container's internal port 8000. This is why the app inside the
container can simply bind to `0.0.0.0:8000` without knowing anything about the host
machine's actual IP or port configuration — the kernel-level translation is what
makes "8000:8000" work identically regardless of what else is running on the host.

Inside `docker-compose`'s network, the API reaching the database via the hostname
`db` isn't magic service discovery — Compose creates a private Docker network for
the whole `docker-compose.yml` file and runs an embedded DNS server on it that
resolves each service's name (from the YAML key, `db`) to that container's internal
IP address on the shared network, refreshed automatically as containers restart with
new IPs — ordinary DNS resolution, just scoped to containers on that one
Compose-created network rather than the wider internet.

`needs: test` in the GitHub Actions workflow creates an explicit dependency edge in
the workflow's job graph: GitHub Actions computes which jobs can run in parallel and
which must wait, and a job listed in another's `needs` only starts after that
dependency job's steps have all completed *and* exited successfully (non-zero exit
from any step fails the whole job). `build-and-push` therefore literally cannot
begin — its runner isn't even provisioned — until every step of `test` (including
the `pytest` run) has returned a zero exit code, which is the concrete mechanism
making "broken code can't reach the registry" true rather than aspirational.

## Exercise

Write a `Dockerfile` and `docker-compose.yml` for the Level 3 Book Catalog API
that runs the API alongside a Postgres container (swap the SQLAlchemy URL to
`postgresql://...`), reading `DATABASE_URL` and `SECRET_KEY` from environment
variables with `pydantic-settings`. Then write a GitHub Actions workflow that
runs `pytest` on every push and only builds the Docker image on `main` after
tests pass.
