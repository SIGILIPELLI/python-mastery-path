# 02 · Iterators, Generators & Coroutines

Level 2 introduced generators as a convenient way to produce values lazily.
This module looks underneath: the iterator protocol that `for` loops actually
rely on, how generators implement that protocol automatically, and how
generators can be extended into simple coroutines that receive values, not
just produce them.

## The iterator protocol

A `for` loop over any object relies on two dunder methods working together:
`__iter__` (returns an iterator) and `__next__` (returns the next value, or
raises `StopIteration` when exhausted).

```python
class CountUp:
    """A custom iterable that counts from `start` to `end` inclusive."""

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __iter__(self):
        self.current = self.start
        return self          # this object is its own iterator

    def __next__(self):
        if self.current > self.end:
            raise StopIteration
        value = self.current
        self.current += 1
        return value


for n in CountUp(1, 5):
    print(n)   # 1 2 3 4 5

# what a `for` loop actually does under the hood:
it = iter(CountUp(1, 3))
while True:
    try:
        print(next(it))
    except StopIteration:
        break
```

Separating "iterable" (has `__iter__`) from "iterator" (has `__next__`) means
the same iterable can be iterated multiple times, each producing a fresh
iterator — which is exactly why `CountUp.__iter__` resets `self.current`.

## Generators implement the protocol for you

A generator function automatically produces an object with working
`__iter__` and `__next__` methods — you never have to write `StopIteration`
by hand; it's raised for you when the function returns.

```python
def count_up(start, end):
    current = start
    while current <= end:
        yield current
        current += 1


gen = count_up(1, 3)
print(hasattr(gen, "__iter__"), hasattr(gen, "__next__"))   # True True
print(next(gen), next(gen), next(gen))                        # 1 2 3

try:
    next(gen)
except StopIteration:
    print("exhausted")
```

## Generator internals: `send`, `throw`, `close`

Generators can receive values back through `yield`, not just produce them —
this is what makes them usable as simple coroutines.

```python
def running_average():
    total = 0
    count = 0
    average = None
    while True:
        value = yield average      # pauses here; resumes when send() is called
        total += value
        count += 1
        average = total / count


avg = running_average()
next(avg)                # "prime" the generator — advances to the first yield
print(avg.send(10))       # 10.0
print(avg.send(20))       # 15.0
print(avg.send(30))       # 20.0
avg.close()                # explicitly stop the generator
```

`send(value)` resumes the generator, making the paused `yield` expression
evaluate to `value`, then runs until the next `yield` (or return).

```python
def resilient_worker():
    while True:
        try:
            item = yield
            print(f"processing {item}")
        except ValueError as e:
            print(f"recovered from: {e}")


worker = resilient_worker()
next(worker)
worker.send("task-1")
worker.throw(ValueError("bad task"))   # injects an exception at the paused yield
worker.send("task-2")
```

## Generator pipelines

Because generators are lazy, you can chain several together and nothing runs
until the final consumer pulls values through the whole chain.

```python
def read_lines(lines):
    yield from lines

def non_empty(lines):
    for line in lines:
        if line.strip():
            yield line

def upper(lines):
    for line in lines:
        yield line.upper()


raw = ["hello", "", "  ", "world", ""]
pipeline = upper(non_empty(read_lines(raw)))
print(list(pipeline))   # ['HELLO', 'WORLD']
```

Each stage only processes one item at a time as the consumer pulls it — no
stage builds a full intermediate list.

## `itertools` — building blocks for iterators

The standard library's `itertools` module has efficient, well-tested versions
of common iterator patterns.

```python
import itertools

print(list(itertools.islice(itertools.count(10), 5)))
# [10, 11, 12, 13, 14] — count() is infinite; islice takes just the first 5

print(list(itertools.chain([1, 2], [3, 4])))
# [1, 2, 3, 4] — flatten multiple iterables into one

print(list(itertools.groupby("aaabbbcca")))
# [('a', <itertools._grouper>), ('b', ...), ('c', ...), ('a', ...)]
# groupby only groups CONSECUTIVE equal items — sort first if you need full grouping

for size, group in itertools.groupby("aaabbbcca"):
    print(size, list(group))
```

## Coroutines vs. `async`/`await`

The `send`-based coroutine style above predates Python's native `async def` /
`await` syntax and is rarely written by hand today — but it's the mechanism
`async def` functions are built on. Level 3's
[Concurrency II — Asyncio](05-concurrency-asyncio.md) module covers the modern
`async`/`await` style, which you should reach for in real code.

## Cheat sheet

| Concept | What it does |
|---------|---------------|
| `__iter__` | returns an iterator for an iterable |
| `__next__` | returns the next value or raises `StopIteration` |
| `yield` | pauses a generator function, producing a value |
| `gen.send(value)` | resumes the generator, injecting `value` at the paused `yield` |
| `gen.throw(exc)` | resumes the generator by raising `exc` at the paused `yield` |
| `itertools` | fast, memory-efficient iterator utilities |

## How It Actually Works

`for n in CountUp(1, 5)` compiles to exactly the manual `while`/`try`/`except` loop
shown above — the bytecode instructions are `GET_ITER` (calls `iter(obj)`, which
dispatches to `obj.__iter__()`) followed by a `FOR_ITER` that repeatedly calls the
resulting iterator's `__next__()` and catches `StopIteration` internally to exit the
loop. There's no special-casing for lists vs. custom classes vs. generators here —
anything implementing this exact two-method protocol works identically, which is
also why a `for` loop over a `dict` iterates keys (its `__iter__` yields keys) while
`.items()` returns a *different* iterable/iterator pair.

A generator function's returned object is a genuine implementation of this same
protocol, auto-generated by the interpreter: `count_up.__iter__` just returns `self`,
and `count_up.__next__` resumes the frame execution up to the next `yield` (raising
`StopIteration` when the function body finally returns). What makes `send()` and
`throw()` possible is that this frame is a real, addressable object sitting on the
heap with its own saved instruction pointer and local variables — `gen.send(10)`
resumes execution at exactly the bytecode offset just after the `YIELD_VALUE`
instruction that paused it, but first pushes `10` onto that frame's value stack as
the result of the `yield` *expression* (not just the statement), which is why
`value = yield average` can both produce a value out and receive one in through the
same syntax. `throw()` similarly resumes the frame, but instead of pushing a value it
injects an exception at that exact paused point, letting a `try/except` wrapped
around the `yield` inside the generator catch it — this is precisely the low-level
mechanism `async def` coroutines and `await` were later built on top of (an `await`
is, underneath, a `yield` that suspends the frame back to an event loop instead of to
manual caller code).

`itertools.count(10)` and similar functions are implemented in C as lightweight
iterator objects holding just a counter and a step — no list is ever materialized,
which is why `islice(itertools.count(10), 5)` can safely pull 5 values from an
infinite sequence: `islice` calls `next()` exactly 5 times and then stops, discarding
the (never-ending) rest. `groupby` works by keeping only the *previous* item and
comparing it to each new one as it's pulled — it has no memory of anything before
that, which is mechanically why it only merges runs of *consecutive* equal items
rather than doing a full grouping the way `collections.Counter` or a dict-based
grouping would.

## Exercise

Write a class-based iterator `Fibonacci(limit)` that yields Fibonacci numbers
up to `limit` using the `__iter__`/`__next__` protocol directly (no `yield`).
Then rewrite it as a generator function and confirm both produce identical
output. Finally, write a generator-based coroutine `moving_max()` that accepts
values via `send()` and always yields back the maximum value seen so far.
