# 09 · Packaging & Distribution

Once code is useful beyond a single script, packaging it properly lets others
(`pip install your_package`) — or your future self — reuse it cleanly. This
module covers the modern `pyproject.toml`-based packaging workflow and
publishing to PyPI.

## Project layout for a distributable package

```text
my_package/
    pyproject.toml
    README.md
    LICENSE
    src/
        my_package/
            __init__.py
            core.py
    tests/
        test_core.py
```

The `src/` layout (package code lives inside `src/my_package/`, not directly
next to `pyproject.toml`) is the modern recommendation — it prevents tests
from accidentally importing your local uninstalled source instead of the
actually-installed package.

## `pyproject.toml`

`pyproject.toml` is the single, standardized configuration file for modern
Python packaging — it replaces the older `setup.py`/`setup.cfg` approach.

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "0.1.0"
description = "A small, useful utility library."
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"},
]
dependencies = [
    "requests>=2.31,<3.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "black>=24.0"]

[project.urls]
Homepage = "https://github.com/you/my-package"

[project.scripts]
my-cli = "my_package.core:main"

[tool.setuptools.packages.find]
where = ["src"]
```

`[project.scripts]` above registers a console command: after installing the
package, running `my-cli` in a terminal calls `my_package.core.main()`
directly.

## `src/my_package/core.py`

```python
# src/my_package/core.py

def greet(name: str) -> str:
    return f"Hello, {name}!"


def main():
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "world"
    print(greet(name))
```

## `src/my_package/__init__.py`

```python
# src/my_package/__init__.py
from .core import greet

__version__ = "0.1.0"
__all__ = ["greet"]
```

## Installing locally in "editable" mode

While developing, install your own package so changes to the source are
picked up immediately, without reinstalling after every edit.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # editable install + the "dev" extras group

my-cli Ada        # Hello, Ada!
python -c "from my_package import greet; print(greet('World'))"
```

## Building distributable artifacts

```bash
pip install build
python -m build
```

This produces two files in `dist/`:

```text
dist/
    my_package-0.1.0-py3-none-any.whl   # a "wheel" — the modern binary distribution format
    my_package-0.1.0.tar.gz              # a source distribution ("sdist")
```

## Publishing to PyPI

```bash
pip install twine

# always test on TestPyPI first
twine upload --repository testpypi dist/*

# once verified, publish for real
twine upload dist/*
```

Both uploads require an account and an API token (PyPI no longer accepts
plain username/password uploads) — generate one from your PyPI account
settings and store it in `~/.pypirc` or pass it via environment variable, never
committed to source control.

## Versioning

Semantic versioning (`MAJOR.MINOR.PATCH`) communicates the *kind* of change in
each release to anyone depending on your package.

| Change | Bump |
|--------|------|
| Backward-incompatible API change | MAJOR (`1.x.x` -> `2.0.0`) |
| New backward-compatible feature | MINOR (`1.2.x` -> `1.3.0`) |
| Backward-compatible bug fix | PATCH (`1.2.3` -> `1.2.4`) |

## `.gitignore` essentials for a packaged project

```text
.venv/
__pycache__/
*.egg-info/
dist/
build/
.pytest_cache/
```

## Cheat sheet

| Task | Command |
|------|---------|
| Editable install for development | `pip install -e ".[dev]"` |
| Build wheel + sdist | `python -m build` |
| Upload to TestPyPI | `twine upload --repository testpypi dist/*` |
| Upload to real PyPI | `twine upload dist/*` |

## Exercise

Take the `Stack` class you wrote in Level 2's testing exercise and turn it
into a real installable package: create the `src/`-layout structure above, a
`pyproject.toml` with your package metadata, and a `[project.scripts]` entry
point exposing a tiny CLI that pushes some numbers and prints them popped off
in order. Install it in editable mode and confirm the console command works,
then run `python -m build` and inspect the resulting `dist/` files.
