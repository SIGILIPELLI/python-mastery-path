# 02 · Variables, Data Types & Operators

## Variables

Python variables are just names bound to objects — no type declaration needed.

```python
age = 25
name = "Ada"
height = 1.68
is_student = False
```

## Core built-in types

```python
whole_number = 42          # int
pi_ish = 3.14159            # float
message = "hi there"        # str
flag = True                 # bool
nothing = None               # NoneType

print(type(whole_number))   # <class 'int'>
```

## Numeric operators

```python
a, b = 7, 2

print(a + b)   # 9   addition
print(a - b)   # 5   subtraction
print(a * b)   # 14  multiplication
print(a / b)   # 3.5 true division (always float)
print(a // b)  # 3   floor division
print(a % b)   # 1   modulo (remainder)
print(a ** b)  # 49  exponentiation
```

## Comparison & boolean operators

```python
print(5 > 3)          # True
print(5 == 5.0)       # True (value equality)
print(5 is 5.0)       # False (different objects/types)

print(True and False) # False
print(True or False)  # True
print(not True)       # False
```

## Type conversion

```python
str(42)        # "42"
int("42")      # 42
float("3.5")   # 3.5
int(3.9)       # 3 (truncates, doesn't round)
bool(0)        # False
bool("")       # False
bool("x")      # True — any non-empty string is truthy
```

## Naming rules & convention

- Names use `snake_case` by convention (`user_age`, not `UserAge`).
- Must start with a letter or underscore, can't start with a digit.
- Constants are written `UPPER_SNAKE_CASE` (`MAX_RETRIES = 3`) by convention —
  Python doesn't enforce true immutability here.

## Exercise

Write a script that stores a rectangle's `width` and `height`, computes its area
and perimeter, and prints both formatted to 2 decimal places.
