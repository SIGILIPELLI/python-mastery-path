# 04 · Concurrency I — Threading & Multiprocessing

When a program needs to do more than one thing "at once," Python offers two
very different tools depending on *what kind* of work is involved:
`threading` for I/O-bound work, and `multiprocessing` for CPU-bound work. This
module explains why the split exists, starting with the GIL.

## The Global Interpreter Lock (GIL)

CPython's Global Interpreter Lock allows only one thread to execute Python
bytecode at a time, even on a multi-core machine. This means threads do *not*
give you parallel speedup for CPU-heavy pure-Python code.

```python
import threading
import time

def cpu_bound(n):
    count = 0
    for _ in range(n):
        count += 1
    return count

start = time.perf_counter()
threads = [threading.Thread(target=cpu_bound, args=(20_000_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"threaded: {time.perf_counter() - start:.2f}s")   # not much faster than sequential
```

However, the GIL is released during I/O waits (network calls, disk reads,
`time.sleep`), which is exactly why threading *does* help for I/O-bound work.

## `threading` — good for I/O-bound work

```python
import threading
import time

def download_simulated(name, delay):
    print(f"{name}: starting")
    time.sleep(delay)         # simulates waiting on a network response — GIL is released here
    print(f"{name}: done")


start = time.perf_counter()
threads = [
    threading.Thread(target=download_simulated, args=(f"file-{i}", 1))
    for i in range(5)
]
for t in threads:
    t.start()
for t in threads:
    t.join()   # wait for all threads to finish

print(f"total: {time.perf_counter() - start:.2f}s")   # ~1s, not ~5s — they waited concurrently
```

## Race conditions and locks

Multiple threads mutating shared state without coordination causes race
conditions — the classic bug being a shared counter that ends up wrong because
two threads read-modify-write it at overlapping times.

```python
import threading

counter = 0
lock = threading.Lock()

def increment(n):
    global counter
    for _ in range(n):
        with lock:      # only one thread can hold the lock at a time
            counter += 1


threads = [threading.Thread(target=increment, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)   # 400000 — correct, because the lock serializes the increments
```

Removing `with lock:` above would likely produce a number *less* than
400000, since increments can be lost when two threads interleave their
read-modify-write steps.

## `multiprocessing` — good for CPU-bound work

Each process gets its own Python interpreter and its own GIL, so
`multiprocessing` gives genuine parallelism across CPU cores — at the cost of
higher memory use and the need to explicitly pass data between processes
(since they don't share memory by default).

```python
import multiprocessing
import time

def cpu_bound(n):
    count = 0
    for _ in range(n):
        count += 1
    return count


if __name__ == "__main__":
    start = time.perf_counter()
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(cpu_bound, [20_000_000] * 4)
    print(f"multiprocessing: {time.perf_counter() - start:.2f}s")   # noticeably faster on multi-core machines
```

The `if __name__ == "__main__":` guard is required for multiprocessing on
some platforms — worker processes re-import your script, and without the
guard they'd try to spawn their own pools recursively.

## `concurrent.futures` — a unified, higher-level API

`concurrent.futures` provides `ThreadPoolExecutor` and `ProcessPoolExecutor`
with the same interface, so switching between threads and processes is a
one-line change once your work is expressed as a function.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

def fetch_length(url):
    # pretend this makes a real HTTP request
    import time
    time.sleep(0.5)
    return len(url)


urls = ["https://a.com", "https://b.com", "https://c.com"]

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(fetch_length, url): url for url in urls}
    for future in as_completed(futures):
        url = futures[future]
        print(url, "->", future.result())
```

Swapping `ThreadPoolExecutor` for `ProcessPoolExecutor` above would run each
`fetch_length` call in a separate process instead of a thread — useful the
moment the work becomes CPU-bound instead of I/O-bound.

## `executor.map` — simpler, ordered results

```python
from concurrent.futures import ThreadPoolExecutor

def square(n):
    return n * n

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(square, range(10)))

print(results)   # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81], in the original order
```

## Choosing the right tool

| Workload | Tool | Why |
|----------|------|-----|
| Waiting on network/disk (I/O-bound) | `threading` / `ThreadPoolExecutor` | GIL releases during I/O waits; low overhead |
| Heavy computation (CPU-bound) | `multiprocessing` / `ProcessPoolExecutor` | true parallelism across cores, sidesteps the GIL |
| Many concurrent I/O tasks, single-threaded | `asyncio` (next module) | avoids thread overhead entirely for I/O-bound work |
| Shared mutable state across threads | `threading.Lock` | prevents race conditions |

## Exercise

Write a function `word_count(text)` that counts words in a string. Simulate
processing 8 large text "documents" (just repeat a string many times) using
both `ThreadPoolExecutor` and `ProcessPoolExecutor`, time each approach, and
explain in a comment why one is faster for this CPU-bound task. Then write a
thread-safe `Counter` class using a `threading.Lock` and prove with multiple
threads incrementing it that the final count is exactly correct.
