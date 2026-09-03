# 10 · Profiling & Performance

"Make it work, make it right, make it fast" — in that order. Before optimizing
anything, measure where time is actually being spent; intuition about
performance is frequently wrong. This module covers Python's built-in
profiling tools and the most common, high-value optimizations.

## `timeit` — measuring small snippets precisely

`timeit` runs a snippet many times and reports the average, avoiding the noise
of a single `time.time()` measurement.

```python
import timeit

# comparing string concatenation approaches
concat_time = timeit.timeit(
    "s = ''\nfor i in range(1000): s += str(i)",
    number=1000,
)
join_time = timeit.timeit(
    "s = ''.join(str(i) for i in range(1000))",
    number=1000,
)

print(f"concat: {concat_time:.4f}s")
print(f"join:   {join_time:.4f}s")   # almost always faster — join avoids repeated copying
```

From the command line:

```bash
python -m timeit "'-'.join(str(n) for n in range(100))"
python -m timeit -s "data = list(range(10000))" "sorted(data)"
```

## `cProfile` — profiling a whole program

`timeit` is for isolated snippets; `cProfile` profiles a real program or
function call and shows where time actually goes, function by function.

```python
import cProfile

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


cProfile.run("fibonacci(28)")
```

```text
         1028457 function calls (4 primitive calls) in 0.312 seconds

   Ordered by: standard name

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
   1028457    0.312    0.000    0.312    0.000 script.py:3(fibonacci)
```

`ncalls` (how often a function ran) and `cumtime` (total time including
functions it calls) are usually the two most useful columns for spotting
where to optimize.

## Profiling from the command line

```bash
python -m cProfile -s cumulative my_script.py
```

`-s cumulative` sorts the output by cumulative time, so the biggest bottleneck
appears near the top.

## Visualizing profiles with `snakeviz`

```bash
pip install snakeviz
python -m cProfile -o profile.out my_script.py
snakeviz profile.out   # opens an interactive browser visualization
```

## Line-by-line profiling

`cProfile` shows time per *function*; `line_profiler` narrows it down to
individual lines, useful once you've identified which function is slow.

```bash
pip install line_profiler
```

```python
# my_script.py
@profile   # only works when run through kernprof — no import needed
def slow_function():
    total = 0
    for i in range(1_000_000):
        total += i * i
    return total
```

```bash
kernprof -l -v my_script.py
```

## Memory profiling

```bash
pip install memory_profiler
```

```python
from memory_profiler import profile

@profile
def build_lists():
    a = [0] * 1_000_000
    b = [x * 2 for x in a]
    return b


build_lists()
```

```bash
python -m memory_profiler my_script.py
```

## Common, high-value optimizations

```python
# 1. Avoid repeated attribute/global lookups inside hot loops
import math

def slow():
    result = []
    for i in range(100_000):
        result.append(math.sqrt(i))    # looks up math.sqrt every iteration
    return result

def faster():
    sqrt = math.sqrt                  # look it up once, outside the loop
    return [sqrt(i) for i in range(100_000)]


# 2. Use built-in functions and comprehensions over manual loops (implemented in C)
def slow_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total

def faster_sum(numbers):
    return sum(numbers)   # implemented in C, much faster for large inputs


# 3. Use sets/dicts for membership tests, not lists
big_list = list(range(100_000))
big_set = set(big_list)

def slow_lookup(x):
    return x in big_list   # O(n) — scans the whole list

def faster_lookup(x):
    return x in big_set     # O(1) average — hash lookup


# 4. Avoid building intermediate lists you only need to iterate once
total = sum(n * n for n in range(1_000_000))     # generator — no intermediate list
# vs
total = sum([n * n for n in range(1_000_000)])   # builds the full list first, wastefully
```

## Measure before *and* after

```python
import timeit

before = timeit.timeit(lambda: slow_sum(list(range(10_000))), number=100)
after = timeit.timeit(lambda: faster_sum(list(range(10_000))), number=100)
print(f"before: {before:.4f}s, after: {after:.4f}s, speedup: {before / after:.1f}x")
```

Never assume an optimization helped — verify with a timing comparison,
because sometimes "obvious" optimizations make no measurable difference (or
even hurt, once you account for overhead).

## Cheat sheet

| Question | Tool |
|----------|------|
| Which of these two snippets is faster? | `timeit` |
| Which function is my program's bottleneck? | `cProfile` (sorted by `cumulative`) |
| Which *line* inside that function is slow? | `line_profiler` |
| Is a function using too much memory? | `memory_profiler` |
| Visualize a whole profile | `snakeviz` |

## How It Actually Works

`timeit` isn't just "call `time.time()` before and after" — a single measurement is
dominated by noise (OS scheduler jitter, other processes, CPU frequency scaling,
garbage collection running mid-measurement), so `timeit` disables the automatic
cyclic garbage collector for the duration of the run specifically to remove one major
source of that noise, executes the snippet the requested number of times in a tight
loop with minimal per-iteration overhead (the code is compiled once into a real
function via `exec`, not re-parsed each iteration), and reports total elapsed time —
which is why comparing two approaches needs the same `number=` for both: the
measurement is a sum over many runs, not a single call.

`cProfile` works by installing a C-level **tracing hook** into the interpreter that
fires on specific low-level events — function call, function return, exception —
which is a real feature of the CPython eval loop (the same hook mechanism
`sys.settrace` and debuggers use, though `cProfile` uses the lighter-weight
`sys.setprofile`, which doesn't fire per-line, only per-call). Each time your
`fibonacci` function is entered, the profiler stamps a start time on that call's
frame; on return, it computes elapsed time and adds it to two running totals for
that function's code object: `tottime` (time in the function's own bytecode,
excluding calls to other functions) and `cumtime` (including everything it called,
which is why a top-level function's `cumtime` can be almost the whole program's
runtime even though its `tottime` is tiny). Because this hook fires on *every* call,
recursive functions like naive Fibonacci — with `2^n`-ish calls — show it: the huge
`ncalls` count in the sample output isn't slow code, it's simply how many times a
C-level counter got incremented.

`sum(numbers)` beats a hand-written accumulation loop mechanically because `sum` is
implemented in C: it walks the underlying array performing additions using C-level
loops and, for common numeric types, uses type-specific fast paths that skip much of
the general-purpose `PyNumber_Add` machinery a `total += n` bytecode sequence
(`LOAD_FAST`, `BINARY_OP`, `STORE_FAST`, dispatch through `__add__`, repeated per
element) would otherwise go through on every iteration. Membership testing on a
`set` versus a `list` isn't a "usually faster" heuristic — it's the same O(1)
hash-table lookup versus O(n) linear scan distinction from Module 5's dict/set
internals: `x in big_set` computes `hash(x)` once and checks one slot (occasionally a
few, on collision), while `x in big_list` calls `__eq__` against every element in
order until a match or the end.

## Exercise

Write two versions of a function that finds all prime numbers up to `n`: one
using a naive nested loop, one using the Sieve of Eratosthenes. Profile both
with `cProfile` for `n = 100_000` and compare `cumtime`. Then use `timeit` to
directly compare `x in a_list` vs. `x in a_set` for membership testing on
50,000 items, and report the speedup factor you measure.
