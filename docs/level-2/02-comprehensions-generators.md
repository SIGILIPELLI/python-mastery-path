# 02 · Comprehensions & Generators

Comprehensions are a compact, readable way to build lists, dicts, and sets from
existing iterables. Generators take the same idea further: instead of building
a whole collection in memory, they produce values one at a time, on demand.

## List comprehensions

```python
numbers = range(10)

squares = [n * n for n in numbers]
evens = [n for n in numbers if n % 2 == 0]
labeled = [f"odd:{n}" if n % 2 else f"even:{n}" for n in numbers]

print(squares)   # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
print(evens)      # [0, 2, 4, 6, 8]
```

The general shape is `[expression for item in iterable if condition]`. The
`if` clause is optional; the conditional expression (`x if cond else y`) is a
separate feature that can be combined with it.

## Nested comprehensions

```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

flattened = [n for row in matrix for n in row]
print(flattened)   # [1, 2, 3, 4, 5, 6, 7, 8, 9]

transposed = [[row[i] for row in matrix] for i in range(3)]
print(transposed)   # [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
```

Read nested comprehensions left to right, in the same order you'd write
equivalent nested `for` loops.

## Dict and set comprehensions

```python
words = ["apple", "fig", "kiwi", "banana", "fig"]

lengths = {w: len(w) for w in words}
print(lengths)   # {'apple': 5, 'fig': 3, 'kiwi': 4, 'banana': 6}

unique_lengths = {len(w) for w in words}
print(unique_lengths)   # {3, 4, 5, 6}

# invert a dict (only safe if values are unique and hashable)
by_length = {v: k for k, v in lengths.items()}
```

## Generator expressions

A generator expression looks like a list comprehension but with parentheses
instead of brackets, and it produces values lazily — one at a time, computed
only when requested.

```python
squares_list = [n * n for n in range(1_000_000)]     # builds the full list now
squares_gen = (n * n for n in range(1_000_000))       # builds nothing yet

print(next(squares_gen))   # 0
print(next(squares_gen))   # 1

total = sum(n * n for n in range(1_000_000))  # no intermediate list at all
```

Generators trade memory for a one-shot iteration: once exhausted, you can't
restart a generator — you'd need to create a new one.

## `yield` and generator functions

Any function containing `yield` becomes a generator function: calling it
doesn't run the body — it returns a generator object that runs the body
incrementally as you iterate it.

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1
    yield "liftoff!"


for value in countdown(3):
    print(value)
# 3
# 2
# 1
# liftoff!
```

Execution pauses at each `yield` and resumes right after it on the next call
to `next()`.

```python
def fibonacci():
    a, b = 0, 1
    while True:               # infinite generator — safe because nothing forces it to finish
        yield a
        a, b = b, a + b


fib = fibonacci()
first_ten = [next(fib) for _ in range(10)]
print(first_ten)   # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

## `yield from`

`yield from` delegates to a sub-iterable, flattening it into the outer
generator's output.

```python
def chain(*iterables):
    for iterable in iterables:
        yield from iterable


print(list(chain([1, 2], "ab", (True, False))))
# [1, 2, 'a', 'b', True, False]
```

## Comprehensions vs. generators — when to use which

| Situation | Use |
|-----------|-----|
| Need the result more than once, or need indexing/`len()` | list/dict/set comprehension |
| Result feeds a single pass (`sum`, `for`, `join`) | generator expression |
| Very large or infinite sequence | generator expression or `yield` function |
| Need to pause/resume complex, stateful logic | generator function with `yield` |

## Exercise

Given a large text file (simulate it with a list of strings), write a
generator function `long_lines(lines, min_length)` that yields only the lines
longer than `min_length`, without building an intermediate list. Then use a
generator expression to compute the average length of the lines it yields
without ever materializing them all in memory at once.
