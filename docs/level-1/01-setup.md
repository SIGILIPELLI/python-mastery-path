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

## How It Actually Works

When you type `python3 hello.py`, a lot happens before "Hello, world!" appears:

1. **Interpreter startup.** The OS loads the `python3` executable, which
   initializes the CPython runtime: it sets up the interpreter state, builds
   `sys.path` (from the executable's location, `PYTHONPATH`, and compiled-in
   defaults), and imports a handful of bootstrap modules written in C and
   frozen into the binary.
2. **Reading and compiling your file.** CPython reads `hello.py` as text,
   tokenizes it, parses the tokens into an Abstract Syntax Tree, and compiles
   that AST into **bytecode** — a compact instruction set for CPython's virtual
   machine. Your `def greet` becomes a *code object* holding those
   instructions plus metadata (argument names, constants, line numbers).
3. **`.pyc` caching.** For imported modules CPython writes the compiled
   bytecode to `__pycache__/*.pyc` so it can skip recompilation next time,
   keyed by the source file's hash or mtime. The top-level script you run
   directly is *not* cached this way.
4. **Execution.** CPython creates a module object, sets its `__name__` to
   `"__main__"` (this is the whole reason the `if __name__ == "__main__"`
   guard works), and runs the module's bytecode top to bottom in the
   evaluation loop — a big C `switch` over bytecode instructions. `def greet`
   executes as a "make a function object and bind the name `greet`"
   instruction; the `if` block then calls it.
5. **Shutdown.** After the last instruction, CPython runs cleanup (flushing
   `stdout`, running `atexit` handlers, garbage-collecting), then the process
   exits with status code 0.

The REPL runs this same read → compile → execute loop, but once per line you
type instead of once per file.

## Exercise

Write a script `greet_many.py` that defines a list of three names and prints a
greeting for each one using the `greet` function above.
