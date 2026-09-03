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

## How It Actually Works

The GIL is a single mutex inside the CPython interpreter that must be held by a
thread to execute Python bytecode — it exists because CPython's memory management
(reference counting, specifically) is not thread-safe by design: incrementing and
decrementing an object's refcount from multiple threads simultaneously without a
lock would corrupt it, freeing an object still in use or leaking one that should have
been freed. Rather than adding fine-grained locking to every object (which earlier
experiments showed hurt single-threaded performance badly), CPython uses one global
lock and switches which thread holds it periodically — since Python 3.2, based on a
configurable time interval (`sys.getswitchinterval()`, default ~5ms) rather than a
fixed bytecode-instruction count, giving each thread a fair, tunable slice of actual
execution time.

Crucially, the GIL is released around any operation that calls into blocking C code —
a `socket.recv()`, `time.sleep()`, or file-read system call all release the GIL
before making the OS call and reacquire it after, specifically so other Python
threads can run bytecode while one thread is stuck waiting on the kernel. This is the
precise, mechanical reason threading helps I/O-bound work (the threads spend most of
their time with the GIL released, blocked in the OS) but not CPU-bound pure-Python
work (the threads spend all their time holding the GIL, so the "concurrency" is just
rapid switching between them, not simultaneous execution — four threads doing
`count += 1` in a loop still execute one bytecode instruction at a time, system-wide).

`multiprocessing.Pool` sidesteps the GIL entirely by not sharing a process at all:
each worker is a genuinely separate OS process (started via `fork` on Unix, which
duplicates the parent's memory via copy-on-write, or `spawn`, which starts a fresh
interpreter and re-imports your module) with its own independent memory space, its
own reference counts, and its own GIL — true parallel bytecode execution across
cores. The cost is that arguments and return values crossing the process boundary
(`pool.map(cpu_bound, [...])`) must be **pickled** (serialized to bytes), sent through
an OS pipe to the worker, and unpickled on the other side — this is exactly why the
`if __name__ == "__main__":` guard matters on `spawn`-based platforms: a freshly
started worker process re-imports your script as a module to reconstruct the
functions it needs to call, and without the guard, that re-import would execute your
top-level `Pool(...)` creation code again, recursively spawning more pools.

A `threading.Lock` is a thin wrapper around an OS-level mutex primitive: `with lock:`
calls `lock.acquire()` (blocking the calling thread until it can obtain the lock —
implemented via a semaphore the OS scheduler manages) on entry and `lock.release()`
on exit, guaranteeing that the `counter += 1` read-modify-write sequence (itself
several separate bytecode instructions — a `LOAD_FAST`, a numeric add, a `STORE_FAST`
— any of which the GIL could switch threads between) runs to completion in one
thread before another can start it, which is precisely what a race condition without
the lock is missing.

## Exercise

Write a function `word_count(text)` that counts words in a string. Simulate
processing 8 large text "documents" (just repeat a string many times) using
both `ThreadPoolExecutor` and `ProcessPoolExecutor`, time each approach, and
explain in a comment why one is faster for this CPU-bound task. Then write a
thread-safe `Counter` class using a `threading.Lock` and prove with multiple
threads incrementing it that the final count is exactly correct.
