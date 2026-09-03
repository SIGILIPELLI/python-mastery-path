# 08 · Virtual Environments & Dependencies

Every non-trivial Python project depends on third-party packages, and
different projects on the same machine often need different, incompatible
versions of them. Virtual environments solve this by giving each project its
own isolated set of installed packages.

## Why isolate environments

Without a virtual environment, `pip install` affects your entire system (or
user) Python installation. Project A needing `requests==2.25` and Project B
needing `requests==2.31` would conflict. A virtual environment gives each
project its own private copy of the interpreter's `site-packages`.

## Creating a virtual environment

```bash
# create a virtual environment in a folder called .venv
python3 -m venv .venv

# activate it (macOS/Linux)
source .venv/bin/activate

# activate it (Windows, PowerShell)
.venv\Scripts\Activate.ps1

# your shell prompt now shows (.venv) — confirm which python/pip is active:
which python
which pip
```

While activated, `python` and `pip` refer to the versions inside `.venv`, not
the system ones.

## Installing packages

```bash
pip install requests
pip install "requests>=2.31,<3.0"
pip install requests==2.31.0     # exact version — a "pin"

pip list                          # see everything installed in this environment
pip show requests                 # details about a specific package
```

## Deactivating

```bash
deactivate
```

This returns your shell to using the system/global Python.

## `requirements.txt`

A `requirements.txt` file records exactly which packages (and versions) a
project needs, so anyone else can recreate the same environment.

```bash
# write out everything currently installed, pinned to exact versions
pip freeze > requirements.txt
```

```text
# requirements.txt
requests==2.31.0
click==8.1.7
python-dateutil==2.9.0
```

```bash
# on another machine (after creating & activating a fresh venv):
pip install -r requirements.txt
```

## Pinning strategy

| Style | Example | Trade-off |
|-------|---------|-----------|
| Exact pin | `requests==2.31.0` | fully reproducible, but you won't get bugfixes automatically |
| Compatible range | `requests>=2.31,<3.0` | gets patch/minor updates, avoids breaking major changes |
| Unpinned | `requests` | always latest — convenient for experiments, risky for production |

For applications (not libraries you publish), exact pins in
`requirements.txt` are usually the safest default — they guarantee everyone
and every deployment uses identical versions.

## Separating dev-only dependencies

It's common to split dependencies actually needed to run the app from tools
only needed while developing it (test runners, linters).

```text
# requirements.txt — needed to run the app
requests==2.31.0
click==8.1.7

# requirements-dev.txt — only needed for development
-r requirements.txt
pytest==8.2.0
black==24.4.0
```

```bash
pip install -r requirements-dev.txt
```

## Checking for outdated or vulnerable packages

```bash
pip list --outdated
pip install --upgrade requests
```

## A typical project workflow

```bash
mkdir my_project && cd my_project
python3 -m venv .venv
source .venv/bin/activate
pip install requests click
pip freeze > requirements.txt
echo ".venv/" >> .gitignore    # never commit the virtual environment itself
git init
git add requirements.txt .gitignore
git commit -m "Initial project setup"
```

The `.venv` folder itself should never be committed to version control — it's
large, platform-specific, and fully reproducible from `requirements.txt`.

## How It Actually Works

**A virtual environment is mostly a directory layout plus one config file.**
`python3 -m venv .venv` creates:

- `.venv/bin/python` — a symlink (or small copy) pointing back at the base
  interpreter.
- `.venv/pyvenv.cfg` — a text file recording the `home` (the base Python) and
  `include-system-site-packages = false`.
- `.venv/lib/pythonX.Y/site-packages/` — an empty install target.

The magic is in interpreter startup. When *any* Python starts, it walks up
from its own executable looking for a `pyvenv.cfg`. Finding one, it sets
`sys.prefix` to the venv directory and puts the venv's `site-packages` on
`sys.path` *instead of* the system one. So "activating" is almost cosmetic:
`source .venv/bin/activate` just prepends `.venv/bin` to `$PATH` and sets
`$VIRTUAL_ENV`, so typing `python` finds the venv's interpreter — which would
have used the venv's packages anyway. Running `.venv/bin/python` directly,
with no activation, works identically.

**`pip install requests`** then:

1. Queries the PyPI "simple" index for the `requests` project page, reads the
   list of released files, and picks the best-matching **wheel**
   (`.whl` — a ZIP with a specific naming scheme) for your Python version and
   platform.
2. Recursively resolves dependencies (`urllib3`, `certifi`, `idna`,
   `charset-normalizer`), backtracking if version constraints conflict.
3. Downloads each wheel and unpacks it straight into `site-packages/`, then
   writes a `<pkg>.dist-info/` folder containing `METADATA`, `RECORD` (a
   manifest with hashes of every installed file), and `entry_points.txt`.

`pip freeze` just reads those `dist-info` folders and prints
`name==version` for each; `pip install -r` replays them. The `.venv` folder
is disposable precisely because all of this is reconstructible from
`requirements.txt`.

## Exercise

Starting from an empty folder, create a virtual environment, activate it,
install `requests` and any one other package of your choice, generate a
`requirements.txt` with `pip freeze`, then deactivate and delete the `.venv`
folder entirely. Finally, recreate the environment from scratch using only
`requirements.txt` and confirm `pip list` shows the same packages.
