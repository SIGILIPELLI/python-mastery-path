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

## Exercise

Write a `Dockerfile` and `docker-compose.yml` for the Level 3 Book Catalog API
that runs the API alongside a Postgres container (swap the SQLAlchemy URL to
`postgresql://...`), reading `DATABASE_URL` and `SECRET_KEY` from environment
variables with `pydantic-settings`. Then write a GitHub Actions workflow that
runs `pytest` on every push and only builds the Docker image on `main` after
tests pass.
