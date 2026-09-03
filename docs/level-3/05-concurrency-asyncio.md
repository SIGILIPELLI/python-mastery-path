# 05 · Concurrency II — Asyncio

`asyncio` gives you concurrency for I/O-bound work using a single thread and
an event loop, instead of OS threads. Instead of the operating system
switching between threads, your own code cooperatively yields control at
`await` points — cheaper, and free of the locking concerns from the previous
module.

## `async def` and `await`

```python
import asyncio

async def say_after(delay, message):
    await asyncio.sleep(delay)   # non-blocking sleep — yields control to the event loop
    print(message)
    return message


async def main():
    result = await say_after(1, "hello")
    print(f"got: {result}")


asyncio.run(main())
```

Calling `say_after(1, "hello")` doesn't run the function yet — it creates a
coroutine object. `await` is what actually drives it, running it until
completion (or until it hits its own `await`).

## Why sequential `await` doesn't help concurrency

```python
import asyncio
import time

async def task(name, delay):
    await asyncio.sleep(delay)
    print(f"{name} done")


async def main():
    start = time.perf_counter()
    await task("A", 1)
    await task("B", 1)
    print(f"sequential: {time.perf_counter() - start:.2f}s")   # ~2s — one after another


asyncio.run(main())
```

Awaiting each task one at a time is no different from calling them
synchronously — the concurrency benefit only shows up once you schedule
multiple coroutines to run *together*.

## `asyncio.gather` — run coroutines concurrently

```python
import asyncio
import time

async def task(name, delay):
    await asyncio.sleep(delay)
    print(f"{name} done")
    return name


async def main():
    start = time.perf_counter()
    results = await asyncio.gather(task("A", 1), task("B", 1), task("C", 1))
    print(f"concurrent: {time.perf_counter() - start:.2f}s")   # ~1s — they ran together
    print(results)   # ['A', 'B', 'C']


asyncio.run(main())
```

While one task is inside `asyncio.sleep` (waiting), the event loop runs the
others — all on a single thread.

## Creating and managing tasks

`asyncio.gather` is convenient, but `asyncio.create_task` gives you more
control: the coroutine starts running in the background immediately, and you
choose when (or whether) to await its result.

```python
import asyncio

async def worker(n):
    await asyncio.sleep(0.5)
    return n * n


async def main():
    task1 = asyncio.create_task(worker(2))   # starts running now
    task2 = asyncio.create_task(worker(3))   # also starts running now

    print("tasks are running in the background...")
    result1 = await task1
    result2 = await task2
    print(result1, result2)   # 4 9


asyncio.run(main())
```

## Handling errors in concurrent tasks

By default, `asyncio.gather` cancels remaining tasks and re-raises the first
exception it hits — pass `return_exceptions=True` to instead collect
exceptions alongside successful results.

```python
import asyncio

async def might_fail(n):
    await asyncio.sleep(0.1)
    if n == 2:
        raise ValueError(f"failed on {n}")
    return n * 10


async def main():
    results = await asyncio.gather(
        might_fail(1), might_fail(2), might_fail(3),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            print("error:", r)
        else:
            print("ok:", r)


asyncio.run(main())
# ok: 10
# error: failed on 2
# ok: 30
```

## A realistic pattern: concurrent "fetches" with a limit

Real-world async code often fetches many things concurrently but caps how
many run at once, using a semaphore, to avoid overwhelming a server.

```python
import asyncio
import random

async def fetch(session_id, semaphore):
    async with semaphore:                     # only N fetches run at once
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return f"result-{session_id}"


async def main():
    semaphore = asyncio.Semaphore(3)          # at most 3 concurrent
    tasks = [fetch(i, semaphore) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())
```

## Timeouts

```python
import asyncio

async def slow_operation():
    await asyncio.sleep(5)
    return "finished"


async def main():
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=1)
        print(result)
    except asyncio.TimeoutError:
        print("operation timed out")


asyncio.run(main())
```

## `asyncio` vs. threading vs. multiprocessing

| Situation | Best fit |
|-----------|----------|
| Thousands of concurrent network connections | `asyncio` |
| A handful of blocking I/O calls, existing sync libraries | `threading` |
| Heavy CPU computation | `multiprocessing` |
| Mixing sync (blocking) code into async code | run it in a thread via `loop.run_in_executor` |

## How It Actually Works

`async def` marks a function so that calling it doesn't run any code — it returns a
**coroutine object**, a suspendable frame conceptually identical to a generator's
(in fact, `async def` coroutines and generators share the same underlying frame
machinery in CPython). `asyncio.run(main())` creates an **event loop** — really just
a `while True:` loop running in the current thread — and drives that coroutine object
by repeatedly calling into it and letting it run until it hits an `await` on
something not yet ready, at which point control returns to the loop.

`await asyncio.sleep(delay)` is the crucial mechanism: `asyncio.sleep` doesn't
actually block anything — it registers a callback with the event loop's internal
scheduler (via the OS's timer/`select`/`epoll`/`kqueue` mechanism, whichever the
platform's default loop implementation uses) to be woken up after `delay` seconds,
and then suspends the *coroutine's own frame* right there, handing control back to
the event loop. The loop, now free, checks its list of ready callbacks and other
pending tasks and runs whichever one is ready next — this is why `await
asyncio.sleep(1)` in two coroutines finishes in ~1 second total when run
concurrently (both timers are ticking down in the same loop iteration) rather than 2
seconds sequentially: it's genuinely cooperative multitasking on a *single* OS
thread, with no GIL contention because there's only ever one thread running Python
bytecode at a time by construction, not by lock.

`asyncio.create_task(worker(2))` is what actually schedules a coroutine to run
independently: it wraps the coroutine object in a `Task`, hands it to the event
loop's ready queue immediately, and returns right away — this is different from
`await worker(2)`, which drives the coroutine inline in the current frame and blocks
progress on *this* line until it's done. `asyncio.gather(*coros)` internally wraps
each argument in a `Task` (scheduling all of them essentially at once) and then
awaits all of them together, collecting results in the original order regardless of
completion order — this is exactly why two independently-created tasks can be
"running in the background" between the two lines that create them and the lines
that await them.

A coroutine only ever yields control voluntarily, at an `await` — nothing preempts
it mid-execution the way an OS thread can be preempted between bytecode instructions.
This is why `asyncio.Semaphore(3)` limiting "concurrent" fetches works with none of
`threading.Lock`'s contention concerns: at most 3 coroutines are ever mid-flight
between their own `await` points at once, and since only one Python frame is ever
actually executing at any instant regardless, there's no possibility of two
coroutines corrupting shared state through simultaneous non-atomic mutation the way
threads can — the only hazard is a coroutine holding a resource across an `await`
longer than intended, not a torn read-modify-write.

## Exercise

Write an async function `fetch_all(urls)` that "fetches" each URL by awaiting
`asyncio.sleep(random.uniform(0.2, 0.6))` and returning a fake response
string, running at most 4 concurrently using a `Semaphore`. Add error handling
so that one URL "failing" (raise inside the coroutine for a specific URL)
doesn't stop the others from completing, and print a summary of successes vs.
failures. Time the whole run and confirm it's close to the slowest individual
fetch time, not the sum of all of them.
