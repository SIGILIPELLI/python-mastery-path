# 06 · Strings & Formatting

## String basics

```python
s = "Hello, World!"

print(s.lower())        # hello, world!
print(s.upper())        # HELLO, WORLD!
print(s.replace("World", "Python"))  # Hello, Python!
print(s.split(", "))    # ['Hello', 'World!']
print(" ".join(["a", "b", "c"]))     # a b c
print(s.strip())        # removes leading/trailing whitespace
print(len(s))           # 13
print(s[7:12])          # World
```

## f-strings (preferred formatting method)

```python
name = "Ada"
age = 30
pi = 3.14159265

print(f"{name} is {age} years old")
print(f"pi rounded: {pi:.2f}")        # pi rounded: 3.14
print(f"{age:>5}")                     # right-align in width 5
print(f"{'x' * 3}")                    # expressions work inside f-strings
print(f"{name=}")                      # debug shorthand: name='Ada'
```

## Multi-line strings & raw strings

```python
paragraph = """
This spans
multiple lines.
"""

path = r"C:\Users\ada\data"   # raw string: backslashes aren't escape chars
```

## Common string checks

```python
"42".isdigit()        # True
"hello".startswith("he")  # True
"hello".endswith("lo")    # True
"  ".isspace()         # True
"Hello" in "Hello, World!"  # True (substring test)
```

## Immutability

Strings can't be modified in place — every "modification" returns a new string:

```python
s = "hello"
s.upper()      # returns "HELLO" but doesn't change s
s = s.upper()  # you must reassign to keep the result
```

## How It Actually Works

**A `str` is an immutable array of Unicode code points**, and CPython stores it
compactly using a "flexible string representation" (PEP 393): it picks the
smallest element width the string needs — 1 byte per character if every code
point fits in Latin-1, 2 bytes if it fits in the Basic Multilingual Plane,
4 bytes otherwise. So a plain ASCII string uses 1 byte per character plus a
header; adding one emoji forces the whole string to 4-byte storage. The object
also caches its length and hash.

**Immutability** is enforced because there is simply no bytecode or method that
writes into an existing string's buffer. `s.upper()` allocates a *new* string
object and returns it; `s` still points at the old one until you reassign.
This is what lets CPython safely *intern* strings — identifier-like literals
are stored once in a global table and reused, so `a = "hello"; b = "hello"`
often gives `a is b`.

**f-strings are resolved at compile time, not by parsing at runtime.** The
compiler splits `f"{name} is {age}"` into literal chunks and expression
chunks, compiles each `{...}` as real bytecode, and emits instructions to
evaluate them and join the pieces (via `FORMAT_VALUE`/`BUILD_STRING`, or the
dedicated `FORMAT_SIMPLE`/`FORMAT_WITH_SPEC` opcodes in 3.12+). The
format spec after `:` (like `.2f`) is handed to the value's `__format__`
method. Because it's compiled, an f-string has no dictionary lookup overhead
the way `str.format` or `%` do, and syntax errors inside `{}` are caught when
the file is compiled.

## Exercise

Write a function `slugify(title: str) -> str` that converts `"Hello, World!  "`
into `"hello-world"` — lowercase, punctuation stripped, spaces replaced with
hyphens.
