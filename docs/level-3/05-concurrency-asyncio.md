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

## Exercise

Write an async function `fetch_all(urls)` that "fetches" each URL by awaiting
`asyncio.sleep(random.uniform(0.2, 0.6))` and returning a fake response
string, running at most 4 concurrently using a `Semaphore`. Add error handling
so that one URL "failing" (raise inside the coroutine for a specific URL)
doesn't stop the others from completing, and print a summary of successes vs.
failures. Time the whole run and confirm it's close to the slowest individual
fetch time, not the sum of all of them.
