---
title: "Final Quiz"
description: "Test what you have learned across all four levels of Python Mastery Path with a 20-question final quiz."
---

# Final Quiz

20 questions drawn from all four levels of this course. You need **70% (14 out of 20)** to pass —
you can retake it as many times as you like. Your best result is saved in this browser.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "question": "What does this print?\n```python\ndef f(x, acc=[]):\n    acc.append(x)\n    return acc\nprint(f(1), f(2), f(3, []))\n```\n",
    "options": [
      "[1, 2] [1, 2] [3]",
      "[1] [1, 2] [3]",
      "[1] [2] [3]",
      "[1, 2] [1, 2] [1, 2, 3]"
    ],
    "correctIndex": 0,
    "explanation": "A mutable default argument is created once and shared between calls; the first two results are the same list object. Verified by running it."
  },
  {
    "question": "What does this comprehension and unpacking print?\n```python\na,*mid,z=range(6)\nd={k:v for k,v in zip('abc',[1,2,3]) if v!=2}\nprint(a,mid,z,d)\n```\n",
    "options": [
      "0 [1, 2, 3, 4] 5 {'a': 1, 'c': 3}",
      "0 (1, 2, 3, 4) 5 {'a': 1}",
      "0 [1, 2, 3] 5 {'a': 1, 'c': 3}",
      "0 [1, 2, 3, 4] 5 {'a': 1, 'b': 2, 'c': 3}"
    ],
    "correctIndex": 0,
    "explanation": "Starred assignment collects the middle as a list. Verified by running it."
  },
  {
    "question": "What does this late-binding closure print?\n```python\nfs=[lambda: i for i in range(3)]\ngs=[lambda i=i: i for i in range(3)]\nprint([f() for f in fs],[g() for g in gs])\n```\n",
    "options": [
      "[2, 2, 2] [2, 2, 2]",
      "[2, 2, 2] [0, 1, 2]",
      "[0, 1, 2] [0, 1, 2]",
      "[0, 1, 2] [2, 2, 2]"
    ],
    "correctIndex": 1,
    "explanation": "Closures capture variables, not values; a default argument captures the value now. Verified by running it."
  },
  {
    "question": "What does this generator pipeline print?\n```python\ndef evens(it):\n    for x in it:\n        if x%2==0: yield x\ndef squares(it):\n    for x in it: yield x*x\np=squares(evens(range(10)))\nprint(next(p), sum(p))\n```\n",
    "options": [
      "4 116",
      "0 120",
      "0 116",
      "0 140"
    ],
    "correctIndex": 1,
    "explanation": "Generators are lazy and consumed in order: next took 0 and sum took the remaining 4+16+36+64. Verified by running it."
  },
  {
    "question": "What does this context manager print?\n```python\nfrom contextlib import contextmanager\nout=[]\n@contextmanager\ndef cm(n):\n    out.append(f'enter {n}')\n    try: yield\n    finally: out.append(f'exit {n}')\nwith cm('a'), cm('b'):\n    out.append('body')\nprint(out)\n```\n",
    "options": [
      "['enter b', 'enter a', 'body', 'exit a', 'exit b']",
      "['body']",
      "['enter a', 'enter b', 'body', 'exit a', 'exit b']",
      "['enter a', 'enter b', 'body', 'exit b', 'exit a']"
    ],
    "correctIndex": 3,
    "explanation": "Context managers exit in reverse order. Verified by running it."
  },
  {
    "question": "What does this dataclass do with defaults?\n```python\nfrom dataclasses import dataclass, field\n@dataclass\nclass Cart:\n    items: list = field(default_factory=list)\na,b=Cart(),Cart()\na.items.append(1)\nprint(a.items,b.items)\n```\n",
    "options": [
      "[1] [1]",
      "error",
      "[1] []",
      "[] []"
    ],
    "correctIndex": 2,
    "explanation": "default_factory creates a fresh list per instance. Verified by running it."
  },
  {
    "question": "What does this datetime/timezone code print?\n```python\nfrom datetime import datetime, timezone, timedelta\nt=datetime(2026,3,5,23,30,tzinfo=timezone.utc)\nlocal=t.astimezone(timezone(timedelta(hours=2)))\nprint(local.date(), local.hour, t.date())\n```\n",
    "options": [
      "2026-03-05 1 2026-03-05",
      "2026-03-05 23 2026-03-05",
      "2026-03-06 1 2026-03-05",
      "2026-03-06 23 2026-03-05"
    ],
    "correctIndex": 2,
    "explanation": "Converting zones can change the date. Verified by running it."
  },
  {
    "question": "What does this asyncio code print?\n```python\nimport asyncio\nasync def a(): await asyncio.sleep(0.02); return 'a'\nasync def b(): return 'b'\nasync def main():\n    print(await asyncio.gather(a(),b()), await b())\nasyncio.run(main())\n```\n",
    "options": [
      "['a', 'b'] b",
      "error",
      "['b', 'a'] b",
      "['a'] b"
    ],
    "correctIndex": 0,
    "explanation": "gather preserves the order of its arguments. Verified by running it."
  },
  {
    "question": "What does a parameterised query avoid?\n```python\nimport sqlite3\nc=sqlite3.connect(':memory:'); c.execute('create table t(a)')\nc.execute('insert into t values (?)',(\"x'); DROP TABLE t;--\",))\nprint(c.execute('select count(*) from t').fetchone()[0])\n```\n",
    "options": [
      "error",
      "1",
      "0",
      "2"
    ],
    "correctIndex": 1,
    "explanation": "The malicious text was stored as data, not executed. Verified by running it."
  },
  {
    "question": "When is multiprocessing a better fit than threading in CPython?",
    "options": [
      "For CPU-bound work, because processes are not limited by the GIL",
      "I/O-bound",
      "Always",
      "Never"
    ],
    "correctIndex": 0,
    "explanation": "Threads suit I/O waits."
  },
  {
    "question": "What does `if __name__ == '__main__':` do?",
    "options": [
      "Imports",
      "Tests",
      "Runs the block only when the file is executed directly, not when imported",
      "Defines main"
    ],
    "correctIndex": 2,
    "explanation": "Keeps import side effects away."
  },
  {
    "question": "Why prefer `with open(...)` to a bare open()?",
    "options": [
      "Law",
      "Speed",
      "The file is closed automatically even if an exception occurs",
      "Encoding"
    ],
    "correctIndex": 2,
    "explanation": "Context managers handle cleanup."
  },
  {
    "question": "What is the difference between a list and a tuple?",
    "options": [
      "Same",
      "Tuples are slower",
      "Lists are hashable",
      "Lists are mutable; tuples are immutable (and hashable if their items are)"
    ],
    "correctIndex": 3,
    "explanation": "Use tuples for fixed records."
  },
  {
    "question": "Why use virtual environments?",
    "options": [
      "Speed",
      "Isolate each project's dependencies and versions",
      "Law",
      "Colour"
    ],
    "correctIndex": 1,
    "explanation": "python -m venv .venv."
  },
  {
    "question": "What does pytest discover by default?",
    "options": [
      "Files named test_*.py and functions named test_*",
      "Only classes",
      "Any file",
      "All files"
    ],
    "correctIndex": 0,
    "explanation": "Naming conventions matter."
  },
  {
    "question": "What is the safest way to compare two floats in a test?",
    "options": [
      "==",
      "With a tolerance (math.isclose or pytest.approx)",
      "<",
      "is"
    ],
    "correctIndex": 1,
    "explanation": "Floating-point rounding."
  },
  {
    "question": "What is a decorator?",
    "options": [
      "A class only",
      "A comment",
      "A loop",
      "A callable that takes a function and returns a replacement, applied with @"
    ],
    "correctIndex": 3,
    "explanation": "@d above def f is f = d(f)."
  },
  {
    "question": "What does EAFP mean?",
    "options": [
      "Never use try",
      "Use asserts",
      "Check first always",
      "Easier to ask forgiveness than permission: try the operation and handle the exception"
    ],
    "correctIndex": 3,
    "explanation": "Pythonic style."
  },
  {
    "question": "What should you never do with untrusted input?",
    "options": [
      "eval or exec it, or unpickle it",
      "Escape it",
      "Validate it",
      "Parse it with json"
    ],
    "correctIndex": 0,
    "explanation": "Arbitrary code execution."
  },
  {
    "question": "Why measure before optimising?",
    "options": [
      "Law",
      "Colour",
      "The bottleneck is often not where you expect; profile first",
      "Style"
    ],
    "correctIndex": 2,
    "explanation": "cProfile and timeit."
  }
]
</script>

## Coding challenges

Try these on your own computer, then compare your output. Nothing you write is sent anywhere.

### A log analyser with regex, dataclasses and generators

Parse web-service log lines into immutable Entry objects with a regex with named groups, skipping garbage lines lazily with a generator, then report level counts, slowest paths, the server-error rate, affected users, the time window and the busiest minute using Counter, defaultdict and datetime.

**Starter code**

```python
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

LOG = """\
2026-03-01T10:00:01Z INFO  web  GET /home 200 35ms user=ana
2026-03-01T10:00:02Z ERROR api  POST /pay 500 910ms user=bo
2026-03-01T10:00:03Z INFO  web  GET /cart 200 48ms user=ana
2026-03-01T10:01:10Z WARN  api  GET /items 200 700ms user=cy
2026-03-01T10:01:11Z ERROR api  POST /pay 500 880ms user=bo
this line is garbage
2026-03-01T10:02:00Z INFO  web  GET /home 404 12ms user=di
2026-03-01T10:02:30Z INFO  api  GET /items 200 95ms user=ana
"""

# TODO: PATTERN - a compiled regex with named groups ts, level, svc, method, path, status, ms, user
# TODO: @dataclass(frozen=True) class Entry (ts as datetime, level, service, method, path, status:int, ms:int, user)
# TODO: parse(lines) -> generator of Entry, silently skipping lines that do not match
# Then print, in this order:
#   "parsed N of M lines", level counts (sorted dict), the two slowest paths by average ms (rounded),
#   the server error rate (status >= 500) with one decimal, users with errors, the time window (last - first) and the busiest HH:MM minute

entries = list(parse(LOG.splitlines()))
print("parsed", len(entries), "of", len(LOG.splitlines()), "lines")
print("levels:", dict(sorted(Counter(e.level for e in entries).items())))

by_path = defaultdict(list)
for e in entries:
    by_path[e.path].append(e.ms)
slowest = sorted(((sum(v) / len(v), p) for p, v in by_path.items()), reverse=True)[:2]
print("slowest paths:", [(p, round(avg)) for avg, p in slowest])

errors = [e for e in entries if e.status >= 500]
print("server error rate: {:.1f}%".format(100 * len(errors) / len(entries)))
print("users with errors:", sorted({e.user for e in errors}))
first, last = entries[0].ts, entries[-1].ts
print("window:", last - first)
busiest = Counter(e.ts.strftime("%H:%M") for e in entries).most_common(1)[0]
print("busiest minute:", busiest)
```

**Expected output**

```text
parsed 7 of 8 lines
levels: {'ERROR': 2, 'INFO': 4, 'WARN': 1}
slowest paths: [('/pay', 895), ('/items', 398)]
server error rate: 28.6%
users with errors: ['bo']
window: 0:02:29
busiest minute: ('10:00', 3)
```

<details><summary>Show solution and explanation</summary>

<pre><code>import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

LOG = &quot;&quot;&quot;\
2026-03-01T10:00:01Z INFO  web  GET /home 200 35ms user=ana
2026-03-01T10:00:02Z ERROR api  POST /pay 500 910ms user=bo
2026-03-01T10:00:03Z INFO  web  GET /cart 200 48ms user=ana
2026-03-01T10:01:10Z WARN  api  GET /items 200 700ms user=cy
2026-03-01T10:01:11Z ERROR api  POST /pay 500 880ms user=bo
this line is garbage
2026-03-01T10:02:00Z INFO  web  GET /home 404 12ms user=di
2026-03-01T10:02:30Z INFO  api  GET /items 200 95ms user=ana
&quot;&quot;&quot;

PATTERN = re.compile(
    r&quot;(?P&lt;ts&gt;\S+Z) (?P&lt;level&gt;[A-Z]+)\s+(?P&lt;svc&gt;\w+)\s+(?P&lt;method&gt;[A-Z]+) (?P&lt;path&gt;\S+) (?P&lt;status&gt;\d{3}) (?P&lt;ms&gt;\d+)ms user=(?P&lt;user&gt;\w+)&quot;
)

@dataclass(frozen=True)
class Entry:
    ts: datetime
    level: str
    service: str
    method: str
    path: str
    status: int
    ms: int
    user: str

def parse(lines) -&gt; Iterator[Entry]:
    for line in lines:
        m = PATTERN.match(line)
        if not m:
            continue
        g = m.groupdict()
        yield Entry(datetime.fromisoformat(g[&quot;ts&quot;].replace(&quot;Z&quot;, &quot;+00:00&quot;)), g[&quot;level&quot;], g[&quot;svc&quot;], g[&quot;method&quot;], g[&quot;path&quot;], int(g[&quot;status&quot;]), int(g[&quot;ms&quot;]), g[&quot;user&quot;])

entries = list(parse(LOG.splitlines()))
print(&quot;parsed&quot;, len(entries), &quot;of&quot;, len(LOG.splitlines()), &quot;lines&quot;)
print(&quot;levels:&quot;, dict(sorted(Counter(e.level for e in entries).items())))

by_path = defaultdict(list)
for e in entries:
    by_path[e.path].append(e.ms)
slowest = sorted(((sum(v) / len(v), p) for p, v in by_path.items()), reverse=True)[:2]
print(&quot;slowest paths:&quot;, [(p, round(avg)) for avg, p in slowest])

errors = [e for e in entries if e.status &gt;= 500]
print(&quot;server error rate: {:.1f}%&quot;.format(100 * len(errors) / len(entries)))
print(&quot;users with errors:&quot;, sorted({e.user for e in errors}))
first, last = entries[0].ts, entries[-1].ts
print(&quot;window:&quot;, last - first)
busiest = Counter(e.ts.strftime(&quot;%H:%M&quot;) for e in entries).most_common(1)[0]
print(&quot;busiest minute:&quot;, busiest)
</code></pre>

<p>A frozen dataclass gives a cheap, hashable record; the generator keeps parsing lazy and skips bad lines; Counter and defaultdict do the aggregation. The timestamp&#x27;s trailing Z is replaced because fromisoformat needs an explicit offset on older Pythons. Verified by running the solution.</p>
</details>

### An async job runner with retry decorator and bounded concurrency

Write an async retry decorator with exponential backoff (keeping the function name and counting retries), then run eight flaky jobs with a semaphore limiting concurrency to three. Job 7 never succeeds within three attempts and must be reported as failed without stopping the others.

**Starter code**

```python
import asyncio, functools, random, time

def retry(attempts=3, base=0.01, exceptions=(ConnectionError,)):
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            for i in range(attempts):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as e:
                    if i == attempts - 1:
                        raise
                    wrapper.retries += 1
                    await asyncio.sleep(base * 2 ** i)
        wrapper.retries = 0
        return wrapper
    return deco

# TODO: retry(attempts=3, base=0.01, exceptions=(ConnectionError,)) - an async decorator with exponential backoff (base * 2**i),
#       re-raising on the last attempt, keeping the wrapped function's name (functools.wraps) and counting retries on wrapper.retries
random.seed(3)
failures = {2: 2, 5: 1, 7: 9}   # job id -> how many times it fails before succeeding (7 never succeeds within 3 attempts)
attempts_seen = {}

# TODO: @retry(attempts=3) async def fetch(job_id): record the attempt, sleep 0.01, raise ConnectionError while attempts <= failures.get(job_id, 0), else return job_id * 10
# TODO: async def run(ids, limit): a semaphore bounds concurrency; each worker stores ("ok", value) or ("failed", message); return (results, peak concurrency, elapsed)

results, peak, elapsed = asyncio.run(run(range(1, 9), limit=3))
for i in sorted(results):
    print(i, *results[i])
print("peak concurrency:", peak)
print("retries performed:", fetch.retries)
print("finished fast enough:", elapsed < 1.0)
print("attempts per job:", dict(sorted(attempts_seen.items())))
```

**Expected output**

```text
1 ok 10
2 ok 20
3 ok 30
4 ok 40
5 ok 50
6 ok 60
7 failed job 7 flaky
8 ok 80
peak concurrency: 3
retries performed: 5
finished fast enough: True
attempts per job: {1: 1, 2: 3, 3: 1, 4: 1, 5: 2, 6: 1, 7: 3, 8: 1}
```

<details><summary>Show solution and explanation</summary>

<pre><code>import asyncio, functools, random, time

def retry(attempts=3, base=0.01, exceptions=(ConnectionError,)):
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            for i in range(attempts):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as e:
                    if i == attempts - 1:
                        raise
                    wrapper.retries += 1
                    await asyncio.sleep(base * 2 ** i)
        wrapper.retries = 0
        return wrapper
    return deco

random.seed(3)
failures = {2: 2, 5: 1, 7: 9}   # job id -&gt; how many times it fails before succeeding (7 never succeeds within 3 attempts)
attempts_seen = {}

@retry(attempts=3)
async def fetch(job_id):
    attempts_seen[job_id] = attempts_seen.get(job_id, 0) + 1
    await asyncio.sleep(0.01)
    if attempts_seen[job_id] &lt;= failures.get(job_id, 0):
        raise ConnectionError(f&quot;job {job_id} flaky&quot;)
    return job_id * 10

async def run(ids, limit):
    sem = asyncio.Semaphore(limit)
    running = peak = 0
    results = {}
    async def worker(i):
        nonlocal running, peak
        async with sem:
            running += 1
            peak = max(peak, running)
            try:
                results[i] = (&quot;ok&quot;, await fetch(i))
            except ConnectionError as e:
                results[i] = (&quot;failed&quot;, str(e))
            finally:
                running -= 1
    t = time.perf_counter()
    await asyncio.gather(*(worker(i) for i in ids))
    return results, peak, time.perf_counter() - t

results, peak, elapsed = asyncio.run(run(range(1, 9), limit=3))
for i in sorted(results):
    print(i, *results[i])
print(&quot;peak concurrency:&quot;, peak)
print(&quot;retries performed:&quot;, fetch.retries)
print(&quot;finished fast enough:&quot;, elapsed &lt; 1.0)
print(&quot;attempts per job:&quot;, dict(sorted(attempts_seen.items())))
</code></pre>

<p>The decorator re-raises on the final attempt, the semaphore bounds concurrency and each worker converts the final failure into a result instead of letting gather abort. Retries total 5 (2 + 1 + 2). Verified by running the solution (timings are tiny sleeps; only deterministic facts are printed).</p>
</details>
