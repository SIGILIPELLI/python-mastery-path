# 01 · Setup & First Program

## Install Python

Download Python 3.12+ from [python.org](https://www.python.org/downloads/) or use
your OS package manager:

```bash
# macOS (Homebrew)
brew install python

# Ubuntu/Debian
sudo apt install python3 python3-venv

# Windows: use the installer from python.org and check "Add to PATH"
```

Verify the install:

```bash
python3 --version
# Python 3.12.x
```

## The REPL

The REPL (Read-Eval-Print Loop) is an interactive Python shell — great for quick
experiments:

```bash
python3
>>> 2 + 2
4
>>> print("hello")
hello
>>> exit()
```

## Your first script

Create `hello.py`:

```python
# hello.py
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("world"))
```

Run it:

```bash
python3 hello.py
# Hello, world!
```

`if __name__ == "__main__":` guards code so it only runs when the file is executed
directly, not when it's imported by another module (covered in [Module 9](09-modules-packages.md)).

## Choosing an editor

Any of these work well for this program: VS Code (free, huge Python extension
ecosystem), PyCharm Community (free, Python-specific), or even a plain text editor
plus the terminal. Pick one and move on — the editor matters far less than practice.

## Exercise

Write a script `greet_many.py` that defines a list of three names and prints a
greeting for each one using the `greet` function above.
