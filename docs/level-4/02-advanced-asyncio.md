# 02 · Advanced Asyncio Patterns

Level 3 covered the basics of `async`/`await`, `gather`, and semaphores. This
module goes into patterns needed for production-grade concurrent code:
structured concurrency with task groups, cancellation, and avoiding the
classic pitfalls of unmanaged background tasks.

## The problem with unmanaged tasks

```python
import asyncio

async def background_job():
    await asyncio.sleep(1)
    raise ValueError("something went wrong")


async def main():
    asyncio.create_task(background_job())   # fire-and-forget — dangerous!
    await asyncio.sleep(2)
    print("main finished")


asyncio.run(main())
# main finished
# (the ValueError inside background_job is silently swallowed — or reported
#  late, to stderr, as "Task exception was never retrieved")
```

A task created but never awaited can fail silently, or leak — it keeps
running even if the code that spawned it has moved on or forgotten about it.
This is exactly what structured concurrency is designed to prevent.

## `asyncio.TaskGroup` — structured concurrency (Python 3.11+)

A `TaskGroup` guarantees every task it starts is either awaited to completion
or its failure propagates — no task can be silently forgotten.

```python
import asyncio

async def worker(name, delay, fail=False):
    await asyncio.sleep(delay)
    if fail:
        raise ValueError(f"{name} failed")
    return f"{name} done"


async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker("A", 0.5))
            tg.create_task(worker("B", 0.3))
            tg.create_task(worker("C", 0.2, fail=True))
        print("all tasks succeeded")
    except* ValueError as eg:
        # except* is Python 3.11+ syntax for handling ExceptionGroups
        for exc in eg.exceptions:
            print(f"caught: {exc}")


asyncio.run(main())
# caught: C failed
```

When any task in the group raises, the `TaskGroup` automatically cancels the
remaining sibling tasks and re-raises everything together as an
`ExceptionGroup` — nothing is left running unaccounted for, and nothing is
silently lost.

## Cancellation

Tasks can be cancelled explicitly, and well-written coroutines should handle
that cleanly.

```python
import asyncio

async def long_running():
    try:
        print("starting long work")
        await asyncio.sleep(10)
        print("this line never runs if cancelled")
    except asyncio.CancelledError:
        print("cleaning up after cancellation")
        raise   # convention: re-raise CancelledError after cleanup


async def main():
    task = asyncio.create_task(long_running())
    await asyncio.sleep(1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("confirmed: task was cancelled")


asyncio.run(main())
# starting long work
# cleaning up after cancellation
# confirmed: task was cancelled
```

Always re-raise `CancelledError` after cleanup — swallowing it silently
confuses whatever cancelled the task into thinking it's still running.

## Semaphores, revisited: bounding concurrency

```python
import asyncio

async def fetch_page(page_id, semaphore):
    async with semaphore:
        await asyncio.sleep(0.2)   # simulated I/O
        return f"page-{page_id}"


async def main():
    semaphore = asyncio.Semaphore(5)   # at most 5 concurrent "fetches"
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_page(i, semaphore)) for i in range(20)]

    results = [t.result() for t in tasks]
    print(len(results), "pages fetched")


asyncio.run(main())
```

## Timeouts with `asyncio.timeout` (Python 3.11+)

```python
import asyncio

async def slow_operation():
    await asyncio.sleep(5)
    return "done"


async def main():
    try:
        async with asyncio.timeout(1):
            result = await slow_operation()
            print(result)
    except TimeoutError:
        print("operation timed out and was cancelled cleanly")


asyncio.run(main())
```

`asyncio.timeout` is a context manager version of `wait_for`, and composes
more naturally with `TaskGroup` — a timeout applied around a whole group of
tasks cancels all of them together if it expires.

## Producer/consumer with `asyncio.Queue`

```python
import asyncio

async def producer(queue, count):
    for i in range(count):
        await asyncio.sleep(0.1)
        await queue.put(i)
        print(f"produced {i}")
    await queue.put(None)   # sentinel value signaling "no more items"


async def consumer(queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        print(f"consumed {item}")
        queue.task_done()


async def main():
    queue = asyncio.Queue(maxsize=5)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(queue, 5))
        tg.create_task(consumer(queue))


asyncio.run(main())
```

`asyncio.Queue` handles the coordination between producer and consumer
coroutines safely, including backpressure via `maxsize`.

## Cheat sheet

| Tool | Use |
|------|-----|
| `asyncio.TaskGroup()` | run multiple tasks with guaranteed cleanup/propagation |
| `except*` | handle an `ExceptionGroup` raised by a `TaskGroup` |
| `task.cancel()` | request cancellation of a running task |
| `asyncio.timeout(seconds)` | cancel a block of code if it runs too long |
| `asyncio.Queue` | coordinate producer/consumer coroutines |
| `asyncio.Semaphore(n)` | cap how many coroutines run concurrently |

## How It Actually Works

A fire-and-forget `asyncio.create_task(...)` fails silently because of exactly how
task results are stored: a `Task` object holds its outcome (return value or raised
exception) internally once its coroutine finishes, but nothing ever *reads* that
outcome unless something calls `.result()` or `await`s the task. If the task raised
and nobody ever retrieves that result, the exception just sits there — the event
loop's garbage collector eventually notices the exception was never fetched when the
`Task` object itself is finally collected, and only *then* logs the "Task exception
was never retrieved" warning, which is why it can appear seemingly late and
disconnected from where the actual failure happened.

`asyncio.TaskGroup` fixes this by tracking every task created through `tg.create_task`
in an internal set for the lifetime of the `async with` block. Its `__aexit__`
(the async version of `__exit__` from Level 2's context managers) does not return
until every tracked task has finished, and if any of them raised, it actively calls
`.cancel()` on every other still-running sibling task before re-raising — collecting
every exception that occurred (including from cancellation cleanup) into a single
**`ExceptionGroup`**, a real container type (added in 3.11) that can hold multiple
unrelated exceptions at once, since more than one task can legitimately fail
independently. `except* ValueError` is special *syntax*, not a smarter `except`: it
partitions the group's exceptions by type, handles the matching subset, and
re-raises a new `ExceptionGroup` containing whatever didn't match — enabling
selective handling across a naturally plural failure.

`task.cancel()` doesn't forcibly stop a coroutine's execution the instant it's
called — it schedules a `CancelledError` to be raised *at the next `await` point*
inside that coroutine's frame, using the exact same "inject an exception into a
suspended frame" mechanism as `generator.throw()` from Module 2. This is why
`long_running`'s `try/except CancelledError` block only sees the exception once
control returns to its `await asyncio.sleep(10)` line — cancellation is cooperative,
not preemptive, so a coroutine stuck in a long synchronous computation with no
`await` inside it cannot be cancelled until it reaches one.

`asyncio.Queue` coordinates producer and consumer safely without any lock because
`put`/`get` are themselves coroutines that suspend at `await` when the queue is
full/empty respectively — the queue's internal waiting logic uses `asyncio`'s own
event objects to wake up a waiting `get()` the moment an item is `put()` (and vice
versa for a full queue blocking `put()`), all scheduled through the same single-
threaded event loop, so there's no possibility of the classic race condition between
"check if empty" and "take an item" that a hand-rolled queue on a list would have
under real thread-based concurrency.

## Exercise

Build a small "web crawler" simulation: a `TaskGroup` that fetches 15 fake
"pages" (each an `async def` sleeping a random short duration), bounded by a
`Semaphore(4)`, with an overall `asyncio.timeout(2)` around the whole group.
Make one page's coroutine randomly raise an exception, and use `except*` to
report exactly which page(s) failed versus which timed out versus which
succeeded, with each outcome counted separately.
