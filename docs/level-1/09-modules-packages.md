# 09 · Modules, Packages & pip

## Importing from the standard library

```python
import math
from datetime import date
from collections import Counter

print(math.sqrt(16))         # 4.0
print(date.today())
print(Counter(["a", "b", "a"]))  # Counter({'a': 2, 'b': 1})
```

## Writing your own module

`shapes.py`:

```python
# shapes.py
def area_circle(radius):
    return 3.14159 * radius ** 2

def area_square(side):
    return side ** 2
```

`main.py`, in the same folder:

```python
import shapes

print(shapes.area_circle(2))
print(shapes.area_square(3))

# or import specific names:
from shapes import area_circle
print(area_circle(2))
```

## Packages (folders of modules)

```text
myapp/
    __init__.py
    shapes.py
    utils.py
```

`__init__.py` marks the folder as a package (can be empty). Then:

```python
from myapp import shapes
from myapp.utils import helper_function
```

## Virtual environments

Every project should have its own isolated environment so dependencies don't
clash between projects:

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install requests
pip freeze > requirements.txt  # save exact dependency versions
pip install -r requirements.txt  # recreate the environment elsewhere
deactivate
```

## Installing third-party packages with pip

```bash
pip install requests
```

```python
import requests

response = requests.get("https://api.github.com")
print(response.status_code)  # 200
```

## How It Actually Works

`import shapes` runs the **import system**, and the single most important fact
is that a module's code runs *once per process*:

1. **Cache check.** Python looks up `"shapes"` in `sys.modules`, a dict of
   every module already imported. A hit returns immediately — this is why
   circular imports don't loop forever and why a module is a natural
   singleton.
2. **Finding.** On a miss, Python asks each *finder* in `sys.meta_path`. The
   path-based finder walks `sys.path` (current dir / script dir, then
   `PYTHONPATH`, then the standard library, then `site-packages`) looking for
   `shapes.py`, a `shapes/` package with `__init__.py`, a C extension, etc.
3. **Loading.** The matching *loader* reads the source, checks for a valid
   cached `__pycache__/shapes.cpython-XY.pyc` (compares source mtime/hash and
   Python version), compiles it if stale, and writes the `.pyc` back.
4. **Execution.** Python creates an empty module object, inserts it into
   `sys.modules` *first* (so partial circular imports can see it), then
   executes the module body top to bottom in that module's namespace. `def`s
   and assignments populate the module's `__dict__`.
5. **Binding.** Finally the name `shapes` is bound in *your* namespace to that
   module object. `from shapes import area_circle` does the same load, then
   copies just that one attribute into your namespace.

`__init__.py` is simply the code that runs when a package is first imported.
`pip install requests` downloads a wheel and unpacks it into `site-packages/`,
which is already on `sys.path` — so `import requests` then just works via the
same five steps.

## Exercise

Split a script that manages a to-do list into two modules: `storage.py`
(load/save the list to a JSON file) and `main.py` (the CLI logic that imports
`storage`). This sets up the project for Module 10.
