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

## Exercise

Split a script that manages a to-do list into two modules: `storage.py`
(load/save the list to a JSON file) and `main.py` (the CLI logic that imports
`storage`). This sets up the project for Module 10.
