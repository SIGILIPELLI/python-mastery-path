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

## How It Actually Works

`pip install -e .` ("editable install") doesn't copy your source into
`site-packages` the way a normal install does — it registers a small pointer instead
(historically an `.egg-link` file plus a `.pth` file; modern `pip`/`setuptools` use a
PEP 660-compliant import hook shipped as a tiny generated package). Either mechanism
causes `sys.path` to include your `src/` directory directly, so `import my_package`
resolves straight to your working tree's actual files — which is exactly why
editing `core.py` and rerunning takes effect immediately with no reinstall step:
there's no copy to go stale.

The `src/` layout matters because of how `sys.path` is built at interpreter startup:
one of its default entries is the current working directory (or the running
script's directory). If your package lived directly next to `pyproject.toml` at the
repo root, running `pytest` from that root could import the *bare source directory*
as a package purely by proximity, silently skipping whatever installed version (with
its dependencies and any C extensions) actually got built — masking packaging bugs
that would only surface for a real end user. Nesting the package under `src/` means
nothing on the default path finds it by accident; only an actual install (editable
or not) makes it importable, so your tests exercise the same import path a real user
gets.

`python -m build` produces two genuinely different artifacts because they solve
different problems: the **sdist** (`.tar.gz`) is essentially your source tree plus
`pyproject.toml` — pip can build a wheel from it locally, running your build backend,
which matters for platforms without a prebuilt wheel or packages with C extensions.
The **wheel** (`.whl`) is a pre-built ZIP archive laid out exactly like a
`site-packages` directory — installing a wheel is just an unzip-and-copy, no build
step at all, which is why wheels install dramatically faster and are what `pip`
prefers whenever one matching your platform and Python version is available. The
`py3-none-any` tag in the wheel's filename declares it's pure Python (works on any
Python 3 minor version, any platform, any ABI) — a package with compiled extensions
would carry a much more specific tag naming the exact CPython version and platform
it was built for.

`[project.scripts]` doesn't wire up a shell alias — during install, `setuptools`
generates a tiny, real executable file (a Python script with a shebang line) named
`my-cli` inside the environment's `bin/` (or `Scripts/` on Windows) directory, whose
entire body is an import of `my_package.core` followed by a call to `main()`. That
file lands on `PATH` because it's inside the same `bin/` directory `python`/`pip`
themselves live in — running `my-cli` at the shell is just executing that generated
script like any other program.

## Exercise

Take the `Stack` class you wrote in Level 2's testing exercise and turn it
into a real installable package: create the `src/`-layout structure above, a
`pyproject.toml` with your package metadata, and a `[project.scripts]` entry
point exposing a tiny CLI that pushes some numbers and prints them popped off
in order. Install it in editable mode and confirm the console command works,
then run `python -m build` and inspect the resulting `dist/` files.
