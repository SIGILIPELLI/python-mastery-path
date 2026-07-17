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

## Exercise

Write a function `slugify(title: str) -> str` that converts `"Hello, World!  "`
into `"hello-world"` — lowercase, punctuation stripped, spaces replaced with
hyphens.
