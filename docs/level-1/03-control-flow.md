# 03 · Control Flow

## if / elif / else

```python
score = 82

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

print(grade)  # B
```

## while loops

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## for loops

Python's `for` iterates over sequences, not index counters:

```python
for fruit in ["apple", "banana", "cherry"]:
    print(fruit)

for i in range(5):        # 0, 1, 2, 3, 4
    print(i)

for i in range(2, 10, 2): # 2, 4, 6, 8
    print(i)
```

## break, continue, else

```python
for n in range(2, 20):
    if n % 7 == 0:
        print(f"first multiple of 7: {n}")
        break
else:
    # runs only if the loop finished WITHOUT break
    print("no multiple of 7 found")

for n in range(10):
    if n % 2 != 0:
        continue  # skip odd numbers
    print(n)
```

## Match statement (Python 3.10+)

Structural pattern matching for cleaner multi-branch logic:

```python
def describe(value):
    match value:
        case 0:
            return "zero"
        case int() if value < 0:
            return "negative int"
        case [x, y]:
            return f"pair: {x}, {y}"
        case {"name": name}:
            return f"has a name: {name}"
        case _:
            return "something else"

print(describe(0))            # zero
print(describe([1, 2]))       # pair: 1, 2
print(describe({"name": "Ada"}))  # has a name: Ada
```

## Exercise

Write a program that prints FizzBuzz for numbers 1–30: multiples of 3 print
"Fizz", multiples of 5 print "Buzz", multiples of both print "FizzBuzz",
otherwise print the number.
