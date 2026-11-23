---
title: "Python Interview Questions and Answers (184 Questions)"
description: "184 Python interview questions with answers and explanations, from beginner to advanced, organised by level. Free, from the Python Mastery Path."
---

# Python Interview Questions and Answers

**184 questions** with the correct answer and a short explanation, organised from beginner (Level 1) to advanced (Level 4). Every question comes from a lesson in the free Python Mastery Path, so you can open the lesson to go deeper.

!!! tip "Practise, don't just read"
    Each lesson also ends with an interactive quiz, and the [final quiz](quiz.md) tests all four levels. Try to answer each question below before reading the answer.

## Level 1 · Entry

### [01 · Setup &amp; First Program](level-1/01-setup.md)

**Q1.** Which command starts an interactive Python session (the REPL) on most systems where Python 3 is installed?

**Answer:** python3

Running python3 (or python / py on Windows) with no file name opens the REPL, where each line you type is executed immediately.

**Q2.** You save print("Hello") in hello.py. How do you run it from a terminal in the same folder?

**Answer:** python3 hello.py

Pass the file path to the interpreter: python3 hello.py. The interpreter reads the file top to bottom and executes it.

**Q3.** In the REPL you type 2 + 3 and press Enter. What happens?

**Answer:** 5 is displayed, because the REPL prints the value of each expression

The REPL evaluates each expression and echoes its value. In a script you would need print() to see it.

**Q4.** Which statement about Python files is correct?

**Answer:** Indentation is part of the syntax, so consistent spaces matter

Python uses indentation to define blocks. PEP 8 recommends 4 spaces per level. Semicolons and braces are not needed.

### [02 · Variables, Data Types &amp; Operators](level-1/02-variables-data-types.md)

**Q5.** What does type(7 / 2) return?

**Answer:** &lt;class 'float'&gt;

The / operator always performs true division and returns a float (3.5). Use // for floor division, which returns an int for int operands.

**Q6.** What is the value of 17 % 5?

**Answer:** 2

% returns the remainder: 17 = 5 × 3 + 2, so 17 % 5 is 2.

**Q7.** What does int("42") + 8 evaluate to?

**Answer:** 50

int("42") converts the string to the integer 42, so the result is 50. Without the conversion, "42" + 8 would raise a TypeError.

**Q8.** Which value is falsy in a boolean context?

**Answer:** 0

The number 0, empty strings, empty containers and None are falsy. The string "0" and the list [0] are non-empty, so they are truthy; -1 is a non-zero number, so it is truthy.

### [03 · Control Flow](level-1/03-control-flow.md)

**Q9.** What does this print?
for i in range(3):
    print(i)

**Answer:** 0, 1 and 2 on separate lines

range(3) produces 0, 1, 2. The stop value is excluded.

**Q10.** When does the else block of a for loop run?

**Answer:** When the loop finishes without hitting break

A loop's else runs after the loop completes normally. If break exits the loop early, the else is skipped. This is handy for search loops.

**Q11.** What does continue do inside a loop?

**Answer:** Skips the rest of the current iteration and moves to the next one

continue jumps straight to the next iteration; break exits the loop.

**Q12.** Which Python version introduced the match statement (structural pattern matching)?

**Answer:** 3.10

match/case arrived in Python 3.10 (PEP 634).

### [04 · Functions &amp; Scope](level-1/04-functions-scope.md)

**Q13.** What does a function return if it reaches the end without a return statement?

**Answer:** None

Every Python function returns a value; without an explicit return it returns None.

**Q14.** Inside def total(*args), what is args?

**Answer:** A tuple of all positional arguments passed

*args collects extra positional arguments into a tuple. **kwargs collects keyword arguments into a dict.

**Q15.** Why is def add(item, items=[]) a common bug?

**Answer:** The default list is created once and shared across calls

Default values are evaluated once, when the function is defined. Use items=None and create a new list inside the function.

**Q16.** Are type hints like def area(r: float) -&gt; float: enforced when the code runs?

**Answer:** No, they are documentation for readers and tools like mypy

The interpreter does not enforce annotations. Type checkers and IDEs use them to catch mistakes before you run the code.

### [05 · Core Data Structures](level-1/05-data-structures.md)

**Q17.** Which built-in type is ordered and immutable?

**Answer:** tuple

Tuples keep their order and cannot be changed after creation. Lists are mutable; sets are unordered.

**Q18.** What does {1, 2, 2, 3} evaluate to?

**Answer:** {1, 2, 3}

Sets store unique items, so the duplicate 2 is dropped.

**Q19.** prices = {"tea": 20}. What does prices.get("coffee", 0) return?

**Answer:** 0

dict.get returns the default (here 0) when the key is missing, instead of raising KeyError like prices["coffee"] would.

**Q20.** nums = [3, 1, 2]. What is the difference between nums.sort() and sorted(nums)?

**Answer:** sort() changes the list in place and returns None; sorted() returns a new list

list.sort() sorts in place and returns None; sorted() leaves the original unchanged and returns a new sorted list.

### [06 · Strings &amp; Formatting](level-1/06-strings-formatting.md)

**Q21.** What does f"{3.14159:.2f}" produce?

**Answer:** 3.14

The format spec .2f rounds to two decimal places.

**Q22.** What is "Python"[1:4]?

**Answer:** "yth"

Slicing includes the start index (1, 'y') and excludes the stop index (4), giving 'yth'.

**Q23.** Why do strings have methods like .upper() that return a new string?

**Answer:** Strings are immutable, so they cannot be changed in place

Strings cannot be modified after creation; methods return new strings, so assign the result: s = s.upper().

**Q24.** Which string is a raw string that keeps backslashes literally?

**Answer:** r"C:\new\folder"

The r prefix disables escape sequences, so \n stays as a backslash and n. That's useful for Windows paths and regular expressions.

### [07 · File I/O Basics](level-1/07-file-io.md)

**Q25.** Why is with open("notes.txt") as f: preferred over calling open() and close() yourself?

**Answer:** The file is closed automatically, even if an error occurs

The with statement uses a context manager that always closes the file when the block ends, including on exceptions.

**Q26.** What does mode "a" do when opening a file?

**Answer:** Appends to the end, creating the file if needed

"a" adds to the end of an existing file (or creates it). "w" truncates and overwrites.

**Q27.** What is the most memory-friendly way to process a large text file line by line?

**Answer:** for line in f:

Iterating over the file object reads one line at a time instead of loading the whole file into memory.

**Q28.** Why pass encoding="utf-8" to open()?

**Answer:** So the file reads and writes the same way on every operating system

Without it, the default encoding depends on the platform. Being explicit avoids surprises with non-English characters.

### [08 · Error Handling Basics](level-1/08-error-handling.md)

**Q29.** Which exception does int("abc") raise?

**Answer:** ValueError

The argument has the right type (a string) but an invalid value for conversion, so Python raises ValueError.

**Q30.** When does the finally block run?

**Answer:** Always, whether or not an exception occurred

finally runs in every case, which makes it the place for cleanup such as closing resources.

**Q31.** Why should you avoid a bare except: clause?

**Answer:** It also catches errors you did not expect, hiding real bugs

A bare except catches everything (even KeyboardInterrupt). Catch the specific exceptions you can handle.

**Q32.** In try / except / else, when does else run?

**Answer:** When the try block raised no exception

else holds code that should run only if try succeeded, keeping the try block small and focused.

### [09 · Modules, Packages &amp; pip](level-1/09-modules-packages.md)

**Q33.** What does python3 -m venv .venv do?

**Answer:** Creates an isolated virtual environment in the .venv folder

venv creates a self-contained environment so each project can have its own package versions.

**Q34.** Which file conventionally lists a project's pip dependencies?

**Answer:** requirements.txt

requirements.txt lists packages (often with versions) and is installed with pip install -r requirements.txt.

**Q35.** What is the purpose of the if __name__ == "__main__": guard?

**Answer:** Run code only when the file is executed directly, not when imported

When a module is imported, __name__ is its module name; when run directly it is "__main__". The guard keeps script-only code from running on import.

**Q36.** from math import sqrt lets you call which?

**Answer:** sqrt(16)

from module import name brings the name directly into your namespace, so you call sqrt(16).

### [10 · Project — CLI To-Do App](level-1/10-project-todo-app.md)

**Q37.** What does this todo-list logic print?

```python
todos=[{'id':1,'title':'a','done':False},{'id':2,'title':'b','done':False}]
def complete(i):
    for t in todos:
        if t['id']==i:
            t['done']=True; return True
    return False
print(complete(2), complete(9), [t['title'] for t in todos if not t['done']])
```

**Answer:** True False ['a']

The function returns False for an unknown id and mutates the matching dict. Verified by running it.

**Q38.** What does saving and loading JSON round-trip give?

```python
import json,tempfile,os
p=os.path.join(tempfile.mkdtemp(),'t.json')
json.dump([{'id':1,'title':'x','done':True}],open(p,'w'))
print(json.load(open(p)))
```

**Answer:** [{'id': 1, 'title': 'x', 'done': True}]

JSON preserves booleans, strings and numbers. Verified by running it.

**Q39.** How should the todo app handle a missing data file on first run?

**Answer:** Treat it as an empty list rather than crashing (catch FileNotFoundError)

Handle the first-run case gracefully.

**Q40.** Why keep storage code separate from the command-line parsing?

**Answer:** So each part can be tested and changed independently

Separation of concerns.

## Level 2 · Intermediate

### [01 · Object-Oriented Programming](level-2/01-oop.md)

**Q41.** What does this class print?

```python
class Animal:
    def __init__(self,name): self.name=name
    def speak(self): return f'{self.name} makes a sound'
class Dog(Animal):
    def speak(self): return super().speak()+' - woof'
d=Dog('Rex')
print(d.speak(), isinstance(d,Animal), Dog.__mro__[1].__name__)
```

**Answer:** Rex makes a sound - woof True Animal

super() calls the parent method; Dog is an Animal. Verified by running it.

**Q42.** What do class and instance attributes do here?

```python
class C:
    count=0
    def __init__(self): C.count+=1; self.id=C.count
a,b=C(),C()
print(C.count,a.id,b.id)
a.count=99
print(C.count,a.count,b.count)
```

**Answer:** 2 1 2
2 99 2

Assigning through an instance creates an instance attribute and shadows the class attribute. Verified by running it.

**Q43.** What does a dataclass generate?

```python
from dataclasses import dataclass
@dataclass(order=True)
class P:
    x:int
    y:int=0
print(P(1,2), P(1,2)==P(1,2), P(1)<P(2))
```

**Answer:** P(x=1, y=2) True True

@dataclass adds __init__, __repr__, __eq__ and (with order=True) comparisons. Verified by running it.

**Q44.** What is the purpose of __repr__?

**Answer:** An unambiguous string representation for developers (used by the REPL and debugging)

__str__ is for display.

### [02 · Comprehensions &amp; Generators](level-2/02-comprehensions-generators.md)

**Q45.** What does this print?

```python
sq=[x*x for x in range(6) if x%2==0]
d={w:len(w) for w in ['a','bb','ccc']}
s={x%3 for x in range(10)}
g=(x for x in range(3))
print(sq,d,sorted(s),next(g),next(g),list(g))
```

**Answer:** [0, 4, 16] {'a': 1, 'bb': 2, 'ccc': 3} [0, 1, 2] 0 1 [2]

A generator is consumed as you iterate it. Verified by running it.

**Q46.** What is the memory difference between a list and a generator?

```python
import sys
print(sys.getsizeof([i for i in range(1000)])>sys.getsizeof((i for i in range(1000))))
```

**Answer:** True

A generator expression stores no items, only its state. Verified by running it.

**Q47.** What does this generator function produce?

```python
def fib(n):
    a,b=0,1
    for _ in range(n):
        yield a
        a,b=b,a+b
print(list(fib(8)), sum(fib(10)))
```

**Answer:** [0, 1, 1, 2, 3, 5, 8, 13] 88

yield pauses the function and resumes on the next request. Verified by running it.

**Q48.** When should you prefer a comprehension to a loop?

**Answer:** For simple transform/filter that builds a collection; use a loop when logic is complex

Readability first.

### [03 · Functional Programming](level-2/03-functional-programming.md)

**Q49.** What does this functional pipeline print?

```python
from functools import reduce, partial
nums=[1,2,3,4,5]
print(list(map(lambda x:x*2,nums)), list(filter(lambda x:x%2,nums)), reduce(lambda a,b:a*b,nums), partial(pow,2)(10))
```

**Answer:** [2, 4, 6, 8, 10] [1, 3, 5] 120 1024

map transforms, filter selects, reduce folds, partial fixes arguments. Verified by running it.

**Q50.** What does sorted with a key function do?

```python
words=['pear','fig','banana','kiwi']
print(sorted(words,key=len), sorted(words,key=lambda w:(-len(w),w)))
```

**Answer:** ['fig', 'pear', 'kiwi', 'banana'] ['banana', 'kiwi', 'pear', 'fig']

The sort is stable, so equal keys keep their original order; a tuple key adds tie-breaks. Verified by running it.

**Q51.** What is a closure here?

```python
def counter():
    n=0
    def inc():
        nonlocal n
        n+=1
        return n
    return inc
a=counter(); b=counter()
print(a(),a(),b())
```

**Answer:** 1 2 1

Each call to counter() creates its own enclosed variable. Verified by running it.

**Q52.** What makes a function 'pure'?

**Answer:** Same inputs always give the same output with no side effects

Pure functions are easy to test.

### [04 · Custom Exceptions &amp; Context Managers](level-2/04-exceptions-context-managers.md)

**Q53.** What does this print?

```python
class AppError(Exception): pass
class NotFound(AppError):
    def __init__(self,key): super().__init__(f'missing {key}'); self.key=key
try:
    raise NotFound('x')
except AppError as e:
    print(type(e).__name__, e, e.key)
finally:
    print('cleanup')
```

**Answer:** NotFound missing x x
cleanup

Catching the base class catches subclasses; finally always runs. Verified by running it.

**Q54.** What does a context manager do on error?

```python
from contextlib import contextmanager
log=[]
@contextmanager
def res(n):
    log.append('open '+n)
    try: yield n
    finally: log.append('close '+n)
try:
    with res('a'):
        raise ValueError('boom')
except ValueError: pass
print(log)
```

**Answer:** ['open a', 'close a']

The finally block of a context manager runs even when the body raises. Verified by running it.

**Q55.** What does raise ... from do?

```python
try:
    try: int('x')
    except ValueError as e: raise RuntimeError('bad config') from e
except RuntimeError as r:
    print(type(r.__cause__).__name__)
```

**Answer:** ValueError

The original exception is kept as __cause__. Verified by running it.

**Q56.** Why define custom exception classes?

**Answer:** Callers can catch specific failures and the names document what can go wrong

Inherit from Exception, not BaseException.

### [05 · Data Formats (CSV/JSON/XML)](level-2/05-data-formats.md)

**Q57.** What does csv.DictReader give you?

```python
import csv,io
r=csv.DictReader(io.StringIO('name,age\nAda,36\nGrace,85\n'))
rows=list(r)
print(rows[0], int(rows[1]['age'])+1)
```

**Answer:** {'name': 'Ada', 'age': '36'} 86

CSV values are strings, so convert numbers yourself. Verified by running it.

**Q58.** What does a JSON round trip do to a tuple and non-string keys?

```python
import json
d={'t':(1,2),'n':None,'ok':True,1:'one'}
s=json.dumps(d)
print(s, json.loads(s))
```

**Answer:** {"t": [1, 2], "n": null, "ok": true, "1": "one"} {'t': [1, 2], 'n': None, 'ok': True, '1': 'one'}

JSON has no tuples and only string keys. Verified by running it.

**Q59.** How do you parse XML with the standard library?

```python
import xml.etree.ElementTree as ET
root=ET.fromstring('<users><u id="1">Ada</u><u id="2">Bo</u></users>')
print([(u.get('id'),u.text) for u in root.findall('u')])
```

**Answer:** [('1', 'Ada'), ('2', 'Bo')]

Attributes use .get; element text uses .text. Verified by running it.

**Q60.** Why open CSV files with newline='' in Python?

**Answer:** So the csv module handles line endings correctly, including newlines inside quoted fields

Documented requirement.

### [06 · Regular Expressions](level-2/06-regular-expressions.md)

**Q61.** What do these regex calls return?

```python
import re
s='user=42 and user=7'
print(re.findall(r'user=(\d+)',s), re.search(r'user=(\d+)',s).span(), re.sub(r'\d+','#',s))
```

**Answer:** ['42', '7'] (0, 7) user=# and user=#

findall returns the groups; search returns the first match object. Verified by running it.

**Q62.** What does a named group give you?

```python
import re
m=re.match(r'(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})','2026-03-05')
print(m.groupdict(), m['y'])
```

**Answer:** {'y': '2026', 'm': '03', 'd': '05'} 2026

Named groups read like dictionary keys. Verified by running it.

**Q63.** What is the difference between greedy and lazy?

```python
import re
s='<a><b>'
print(re.findall(r'<.+>',s), re.findall(r'<.+?>',s))
```

**Answer:** ['&lt;a&gt;&lt;b&gt;'] ['&lt;a&gt;', '&lt;b&gt;']

Greedy matches as much as possible; ? makes it lazy. Verified by running it.

**Q64.** When should you NOT use a regex?

**Answer:** For nested or recursive structures like HTML; use a real parser

Regexes are for regular patterns.

### [07 · Dates &amp; Times](level-2/07-dates-times.md)

**Q65.** What does this date arithmetic print?

```python
from datetime import date, datetime, timedelta
d=date(2026,1,31)
print(d+timedelta(days=30), (date(2026,3,1)-date(2026,2,1)).days, d.strftime('%a %d %b %Y'), date.fromisoformat('2026-03-05').isoweekday())
```

**Answer:** 2026-03-02 28 Sat 31 Jan 2026 4

Subtracting dates gives a timedelta; isoweekday is 1=Monday. Verified by running it.

**Q66.** What is the difference between naive and aware datetimes?

```python
from datetime import datetime, timezone, timedelta
a=datetime(2026,1,1,12,tzinfo=timezone.utc)
b=a.astimezone(timezone(timedelta(hours=5,minutes=30)))
print(b.isoformat(), a==b)
```

**Answer:** 2026-01-01T17:30:00+05:30 True

Aware datetimes compare as the same instant across time zones. Verified by running it.

**Q67.** What does zoneinfo handle that fixed offsets cannot?

```python
from zoneinfo import ZoneInfo
from datetime import datetime
ny=ZoneInfo('America/New_York')
w=datetime(2026,1,15,12,tzinfo=ny); s=datetime(2026,7,15,12,tzinfo=ny)
print(w.utcoffset(), s.utcoffset())
```

**Answer:** -1 day, 19:00:00 -1 day, 20:00:00

Daylight saving changes the offset; named zones know the rules. Verified by running it.

**Q68.** What is a safe way to store timestamps?

**Answer:** As UTC (ISO 8601 or epoch), converting to local time only for display

Avoids DST bugs.

### [08 · Virtual Environments &amp; Dependencies](level-2/08-venvs-dependencies.md)

**Q69.** What does a virtual environment isolate?

**Answer:** Installed packages (and the Python interpreter link) per project, preventing version conflicts

python -m venv .venv.

**Q70.** What does pip freeze &gt; requirements.txt capture?

**Answer:** The exact versions of all installed packages so others can reproduce the environment

Pin versions for reproducibility.

**Q71.** Why not install project dependencies globally?

**Answer:** Different projects need different versions and global installs can break system tools

Use a venv per project.

**Q72.** Which interpreter path does a venv use? (prefix differs from base_prefix inside one)

```python
import sys
print(sys.prefix==sys.base_prefix)
```

**Answer:** True

Outside a venv they are the same; in a venv sys.prefix points at the environment. Verified by running it.

### [09 · Testing Basics (pytest)](level-2/09-testing-basics.md)

**Q73.** What does this pytest-style test logic show?

```python
def add(a,b): return a+b
def test_add():
    assert add(2,3)==5
def test_negative():
    assert add(-1,1)==0
for t in (test_add,test_negative):
    t()
print('passed')
```

**Answer:** passed

A test is a function with assertions; pytest finds and runs it. Verified by running it.

**Q74.** What does pytest.approx-style comparison avoid?

```python
print(0.1+0.2==0.3, abs((0.1+0.2)-0.3)<1e-9)
```

**Answer:** False True

Compare floats with a tolerance. Verified by running it.

**Q75.** What does a fixture-like setup/teardown look like with a generator?

```python
log=[]
def fixture():
    log.append('setup'); yield 'db'; log.append('teardown')
f=fixture(); v=next(f)
log.append('use '+v)
try: next(f)
except StopIteration: pass
print(log)
```

**Answer:** ['setup', 'use db', 'teardown']

pytest fixtures with yield run teardown after the test. Verified by running it.

**Q76.** What makes a test good?

**Answer:** Fast, isolated, deterministic and named for the behaviour it checks

One behaviour per test.

### [10 · Project — Weather/Data CLI](level-2/10-project-weather-cli.md)

**Q77.** What does this safe parsing of an API response do?

```python
data={'main':{'temp':21.456},'name':'Oslo'}
def summary(d):
    try: return f"{d['name']}: {d['main']['temp']:.1f}C"
    except KeyError as e: return f'missing {e.args[0]}'
print(summary(data), summary({'name':'X'}))
```

**Answer:** Oslo: 21.5C missing main

Handle missing keys explicitly and format output. Verified by running it.

**Q78.** How should the CLI handle a failed request?

```python
def fetch(ok):
    if not ok: raise ConnectionError('offline')
    return 'data'
for ok in (True,False):
    try: print(fetch(ok))
    except ConnectionError as e: print('error:',e)
```

**Answer:** data
error: offline

Catch specific errors and show a friendly message. Verified by running it.

**Q79.** Where should the API key come from?

**Answer:** An environment variable or config file kept out of version control

Never commit secrets.

**Q80.** How do you test the client without the network?

**Answer:** Inject or mock the HTTP layer and feed canned responses

Deterministic tests.

## Level 3 · Advanced

### [01 · Advanced OOP](level-3/01-advanced-oop.md)

**Q81.** What does this ABC enforce?

```python
from abc import ABC, abstractmethod
class Shape(ABC):
    @abstractmethod
    def area(self): ...
class Sq(Shape):
    def __init__(s,a): s.a=a
    def area(s): return s.a**2
try: Shape()
except TypeError as e: print('abstract')
print(Sq(3).area())
```

**Answer:** abstract
9

Abstract classes can't be instantiated until all abstract methods are implemented. Verified by running it.

**Q82.** What does __slots__ change?

```python
class P:
    __slots__=('x','y')
    def __init__(s): s.x=1; s.y=2
p=P()
try: p.z=3
except AttributeError: print('no dynamic attrs')
print(hasattr(p,'__dict__'))
```

**Answer:** no dynamic attrs
False

__slots__ removes the per-instance dict, saving memory and blocking new attributes. Verified by running it.

**Q83.** How does a property validate on set?

```python
class T:
    def __init__(s): s._c=0
    @property
    def c(s): return s._c
    @c.setter
    def c(s,v):
        if v<-273.15: raise ValueError('too cold')
        s._c=v
t=T(); t.c=20
try: t.c=-300
except ValueError as e: print(e)
print(t.c)
```

**Answer:** too cold
20

Properties let you add validation without changing the interface. Verified by running it.

**Q84.** What is the MRO?

**Answer:** The method resolution order: the order Python searches classes for an attribute (C3 linearisation)

Check Class.__mro__.

### [02 · Iterators, Generators &amp; Coroutines](level-3/02-iterators-generators-coroutines.md)

**Q85.** What does a custom iterator do?

```python
class Count:
    def __init__(s,n): s.n=n; s.i=0
    def __iter__(s): return s
    def __next__(s):
        if s.i>=s.n: raise StopIteration
        s.i+=1; return s.i
print(list(Count(3)), sum(Count(4)))
```

**Answer:** [1, 2, 3] 10

An iterator implements __iter__ and __next__ and signals the end with StopIteration. Verified by running it.

**Q86.** What does send() do on a generator coroutine?

```python
def acc():
    total=0
    while True:
        x=yield total
        total+=x
g=acc(); next(g)
print(g.send(5), g.send(10))
```

**Answer:** 5 15

send resumes the generator with a value that becomes the result of yield. Verified by running it.

**Q87.** What does yield from do?

```python
def inner():
    yield 1; yield 2
    return 'done'
def outer():
    r=yield from inner()
    yield r
print(list(outer()))
```

**Answer:** [1, 2, 'done']

yield from delegates to a sub-generator and returns its return value. Verified by running it.

**Q88.** Why are generators good for large files?

**Answer:** They stream items one at a time so memory use stays small

Process line by line.

### [03 · Advanced Decorators &amp; Descriptors](level-3/03-decorators-descriptors.md)

**Q89.** What does this decorator with arguments do?

```python
import functools
def repeat(n):
    def deco(f):
        @functools.wraps(f)
        def w(*a,**k):
            return [f(*a,**k) for _ in range(n)]
        return w
    return deco
@repeat(3)
def hi(name): 'greet'; return f'hi {name}'
print(hi('a'), hi.__name__)
```

**Answer:** ['hi a', 'hi a', 'hi a'] hi

functools.wraps preserves the wrapped function's name and docstring. Verified by running it.

**Q90.** What does a descriptor do?

```python
class Positive:
    def __set_name__(s,o,n): s.n='_'+n
    def __get__(s,o,t=None): return getattr(o,s.n)
    def __set__(s,o,v):
        if v<=0: raise ValueError('must be positive')
        setattr(o,s.n,v)
class Item:
    qty=Positive()
    def __init__(s,q): s.qty=q
i=Item(3)
try: i.qty=-1
except ValueError as e: print(e)
print(i.qty)
```

**Answer:** must be positive
3

Descriptors customise attribute access and are reusable across classes. Verified by running it.

**Q91.** What does lru_cache do here?

```python
from functools import lru_cache
calls=0
@lru_cache(maxsize=None)
def f(n):
    global calls; calls+=1
    return n*n
f(3);f(3);f(4)
print(calls, f.cache_info().hits)
```

**Answer:** 2 1

Repeated calls with the same arguments are served from the cache. Verified by running it.

**Q92.** What is a decorator, in one sentence?

**Answer:** A callable that takes a function and returns a (usually wrapped) replacement

@deco is sugar for f = deco(f).

### [04 · Concurrency I — Threading &amp; Multiprocessing](level-3/04-concurrency-threading-multiprocessing.md)

**Q93.** What does the GIL limit in CPython?

**Answer:** Only one thread executes Python bytecode at a time, so threads do not speed up CPU-bound pure-Python code

Use multiprocessing for CPU-bound work.

**Q94.** What does a lock protect here? (the result is deterministic with the lock)

```python
import threading
n=0; lock=threading.Lock()
def work():
    global n
    for _ in range(10000):
        with lock: n+=1
ts=[threading.Thread(target=work) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]
print(n)
```

**Answer:** 40000

The lock makes the read-modify-write atomic. Verified by running it.

**Q95.** What does ThreadPoolExecutor.map return?

```python
from concurrent.futures import ThreadPoolExecutor
import time
def slow(x): time.sleep(0.05); return x*2
with ThreadPoolExecutor(4) as ex:
    print(list(ex.map(slow,[1,2,3,4])))
```

**Answer:** [2, 4, 6, 8]

map preserves input order even though tasks run concurrently. Verified by running it.

**Q96.** Which is better for many slow network calls: threads or processes?

**Answer:** Threads (or asyncio), because the work is I/O-bound and releases the GIL while waiting

Processes are for CPU-bound work.

### [05 · Concurrency II — Asyncio](level-3/05-concurrency-asyncio.md)

**Q97.** What does asyncio.gather do here?

```python
import asyncio,time
async def job(n):
    await asyncio.sleep(0.2); return n
async def main():
    t=time.perf_counter()
    r=await asyncio.gather(job(1),job(2),job(3))
    print(r, time.perf_counter()-t<0.5)
asyncio.run(main())
```

**Answer:** [1, 2, 3] True

The three sleeps overlap, so total time is about one sleep, and results keep argument order. Verified by running it.

**Q98.** What does a timeout look like?

```python
import asyncio
async def slow(): await asyncio.sleep(1)
async def main():
    try: await asyncio.wait_for(slow(),0.05)
    except asyncio.TimeoutError: print('timeout')
asyncio.run(main())
```

**Answer:** timeout

wait_for cancels the awaitable and raises TimeoutError. Verified by running it.

**Q99.** What does a semaphore limit?

```python
import asyncio
cur=0; peak=0
sem=asyncio.Semaphore(2)
async def w():
    global cur,peak
    async with sem:
        cur+=1; peak=max(peak,cur)
        await asyncio.sleep(0.02)
        cur-=1
async def main(): await asyncio.gather(*[w() for _ in range(6)])
asyncio.run(main())
print(peak)
```

**Answer:** 2

A semaphore caps how many tasks run a section at once. Verified by running it.

**Q100.** What blocks the event loop?

**Answer:** CPU-heavy work or blocking calls (time.sleep, requests) inside a coroutine

Use run_in_executor or async libraries.

### [06 · Databases (SQLite &amp; SQLAlchemy)](level-3/06-databases.md)

**Q101.** What does parameterised SQL protect against?

```python
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('create table u(name text)')
c.execute('insert into u values (?)',("Robert'); DROP TABLE u;--",))
print(c.execute('select count(*) from u').fetchone()[0], c.execute('select name from u').fetchone()[0][:6])
```

**Answer:** 1 Robert

Placeholders keep data separate from SQL, so injection text is just a string. Verified by running it.

**Q102.** What does a transaction rollback do?

```python
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('create table a(x int)')
try:
    with c:
        c.execute('insert into a values (1)')
        raise RuntimeError('fail')
except RuntimeError: pass
print(c.execute('select count(*) from a').fetchone()[0])
```

**Answer:** 0

The connection context manager rolls back on exceptions. Verified by running it.

**Q103.** What does a JOIN with GROUP BY return?

```python
import sqlite3
c=sqlite3.connect(':memory:')
c.executescript('create table u(id int,name text);create table o(uid int,amt int);insert into u values (1,"a"),(2,"b");insert into o values (1,10),(1,20),(2,5);')
print(c.execute('select name,sum(amt) from u join o on u.id=o.uid group by name order by name').fetchall())
```

**Answer:** [('a', 30), ('b', 5)]

Join then aggregate per group. Verified by running it.

**Q104.** What does an ORM like SQLAlchemy give you?

**Answer:** Python classes mapped to tables and a query API, at the cost of an abstraction layer

Know the SQL it generates.

### [07 · Consuming APIs](level-3/07-consuming-apis.md)

**Q105.** How do you build query strings safely?

```python
from urllib.parse import urlencode, urlparse, parse_qs
u='https://api.example.com/search?'+urlencode({'q':'a b&c','page':2})
print(u, parse_qs(urlparse(u).query))
```

**Answer:** https://api.example.com/search?q=a+b%26c&amp;page=2 {'q': ['a b&amp;c'], 'page': ['2']}

urlencode escapes special characters; parse_qs returns lists. Verified by running it.

**Q106.** What does response handling look like with a stub?

```python
class R:
    status_code=429; headers={'Retry-After':'2'}
    def json(s): return {}
def handle(r):
    if r.status_code==429: return f"wait {int(r.headers['Retry-After'])}s"
    return r.json()
print(handle(R()))
```

**Answer:** wait 2s

Honour rate-limit responses and Retry-After. Verified by running it.

**Q107.** What does exponential backoff produce?

```python
delays=[min(30,0.5*2**i) for i in range(7)]
print(delays)
```

**Answer:** [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 30]

Double the wait each retry up to a cap, usually with jitter. Verified by running it.

**Q108.** Why always set a timeout on HTTP requests?

**Answer:** Without one a hung server can block your program forever

requests.get(url, timeout=5).

### [08 · Building APIs (Flask/FastAPI)](level-3/08-building-apis.md)

**Q109.** What does this Flask-like route table model do?

```python
routes={}
def route(path,method='GET'):
    def d(f): routes[(method,path)]=f; return f
    return d
@route('/ping')
def ping(): return {'ok':True},200
@route('/items','POST')
def add(): return {'id':1},201
print(routes[('GET','/ping')](), routes[('POST','/items')]()[1], ('GET','/nope') in routes)
```

**Answer:** ({'ok': True}, 200) 201 False

Decorators register handlers by method and path. Verified by running it.

**Q110.** What does request validation return for bad input?

```python
def create(body):
    errs=[]
    if not isinstance(body.get('name'),str) or not body['name'].strip(): errs.append('name required')
    if not isinstance(body.get('qty'),int) or body['qty']<1: errs.append('qty must be >=1')
    return (422,{'errors':errs}) if errs else (201,body)
print(create({'name':'a','qty':2})[0], create({'name':' ','qty':0}))
```

**Answer:** 201 (422, {'errors': ['name required', 'qty must be &gt;=1']})

Validate at the boundary and return all errors with 422. Verified by running it.

**Q111.** What does REST say about resource URLs?

**Answer:** They identify things (nouns), and HTTP methods express the action

GET /users/1 not /getUser?id=1.

**Q112.** What status should a successful creation return?

**Answer:** 201 Created with a Location header or the new resource

Be precise with status codes.

### [09 · Packaging &amp; Distribution](level-3/09-packaging-distribution.md)

**Q113.** What does pyproject.toml hold?

**Answer:** Project metadata, dependencies and build-system configuration

The modern standard for packaging.

**Q114.** What does `pip install -e .` do?

**Answer:** Installs the project in editable mode so code changes take effect without reinstalling

Useful during development.

**Q115.** What does __name__ == '__main__' guard?

```python
import io, contextlib
src="def main(): print('running')\nif __name__=='__main__': main()"
g={'__name__':'lib'}; exec(src,g)
b={'__name__':'__main__'}
buf=io.StringIO()
with contextlib.redirect_stdout(buf): exec(src,b)
print(repr(buf.getvalue()))
```

**Answer:** 'running\n'

The block runs only when executed as a script, not when imported. Verified by running it.

**Q116.** What distinguishes a wheel from an sdist?

**Answer:** A wheel is a prebuilt binary distribution; an sdist is source that needs building

Wheels install faster.

### [10 · Profiling &amp; Performance](level-3/10-profiling-performance.md)

**Q117.** What does timeit show about list vs set membership?

```python
import timeit
l=list(range(5000)); s=set(l)
t1=timeit.timeit('4999 in l',globals={'l':l},number=2000)
t2=timeit.timeit('4999 in s',globals={'s':s},number=2000)
print(t1>t2*10)
```

**Answer:** True

Set lookups are O(1) on average versus O(n) for lists. Verified by running it.

**Q118.** What does cProfile-style counting tell you?

```python
import cProfile,pstats,io
def a(): return sum(range(1000))
def b():
    for _ in range(50): a()
pr=cProfile.Profile(); pr.runcall(b)
s=io.StringIO(); pstats.Stats(pr,stream=s).sort_stats('cumulative')
print(pstats.Stats(pr).total_calls>50)
```

**Answer:** True

Profilers count calls and time per function. Verified by running it.

**Q119.** What is the first rule of optimisation?

**Answer:** Measure first: profile to find the real bottleneck before changing code

Don't optimise blind.

**Q120.** Why prefer algorithmic fixes to micro-optimisations?

**Answer:** Changing O(n^2) to O(n log n) beats shaving constant factors

Big-O dominates for large inputs.

### [11 · Project — REST API + Database](level-3/11-project-rest-api-db.md)

**Q121.** What does this repository pattern return?

```python
import sqlite3
class Repo:
    def __init__(s): s.c=sqlite3.connect(':memory:'); s.c.execute('create table t(id integer primary key, title text)')
    def add(s,title): return s.c.execute('insert into t(title) values (?)',(title,)).lastrowid
    def get(s,i):
        r=s.c.execute('select id,title from t where id=?',(i,)).fetchone()
        return {'id':r[0],'title':r[1]} if r else None
r=Repo(); i=r.add('x')
print(i, r.get(i), r.get(99))
```

**Answer:** 1 {'id': 1, 'title': 'x'} None

Hide SQL behind methods that return plain data. Verified by running it.

**Q122.** Where should business rules live?

**Answer:** In a service layer separate from HTTP handlers and SQL

Easier to test.

**Q123.** How do you test the API without a server?

**Answer:** Use the framework's test client against the app object

Fast and isolated.

**Q124.** How do you evolve the schema safely?

**Answer:** Versioned migrations (Alembic or similar)

Track every change.

## Level 4 · Master

### [01 · Design Patterns in Python](level-4/01-design-patterns.md)

**Q125.** What does the Strategy pattern look like in Python?

```python
def tax_us(a): return a*0.07
def tax_eu(a): return a*0.2
class Cart:
    def __init__(s,tax): s.tax=tax
    def total(s,a): return round(a+s.tax(a),2)
print(Cart(tax_us).total(100), Cart(tax_eu).total(100))
```

**Answer:** 107.0 120.0

Behaviour is a swappable callable. Verified by running it.

**Q126.** What does a simple Observer do?

```python
class Subject:
    def __init__(s): s.subs=[]
    def on(s,f): s.subs.append(f)
    def emit(s,x): [f(x) for f in s.subs]
out=[]
s=Subject(); s.on(out.append); s.on(lambda x: out.append(x*2))
s.emit(5)
print(out)
```

**Answer:** [5, 10]

Subscribers are called when the subject emits. Verified by running it.

**Q127.** What does a registry/factory return?

```python
REG={}
def register(n):
    def d(c): REG[n]=c; return c
    return d
@register('csv')
class Csv: kind='csv'
@register('json')
class Js: kind='json'
def make(n): return REG[n]()
print(make('json').kind, sorted(REG))
```

**Answer:** json ['csv', 'json']

A decorator-built registry maps names to classes. Verified by running it.

**Q128.** When is a pattern a mistake?

**Answer:** When it adds complexity the problem does not need; Python's functions and modules often suffice

Prefer the simplest design.

### [02 · Advanced Asyncio Patterns](level-4/02-advanced-asyncio.md)

**Q129.** What does a TaskGroup (3.11+) do on failure?

```python
import asyncio
async def ok(): await asyncio.sleep(0.05); return 1
async def bad(): raise ValueError('x')
async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok()); tg.create_task(bad())
    except* ValueError as eg:
        print(type(eg).__name__, len(eg.exceptions))
asyncio.run(main())
```

**Answer:** ExceptionGroup 1

One failing task cancels the others and raises an ExceptionGroup. Verified by running it.

**Q130.** How do you bound concurrency with a queue of workers?

```python
import asyncio
async def main():
    q=asyncio.Queue(); res=[]
    for i in range(6): q.put_nowait(i)
    async def worker():
        while not q.empty():
            i=q.get_nowait(); await asyncio.sleep(0.01); res.append(i*i); q.task_done()
    await asyncio.gather(*[worker() for _ in range(3)])
    print(sorted(res))
asyncio.run(main())
```

**Answer:** [0, 1, 4, 9, 16, 25]

A fixed number of workers pull jobs from a shared queue. Verified by running it.

**Q131.** What does cancellation look like?

```python
import asyncio
async def main():
    t=asyncio.create_task(asyncio.sleep(10))
    await asyncio.sleep(0)
    t.cancel()
    try: await t
    except asyncio.CancelledError: print('cancelled', t.cancelled())
asyncio.run(main())
```

**Answer:** cancelled True

Cancelling raises CancelledError inside the task. Verified by running it.

**Q132.** Why not call blocking code directly in a coroutine?

**Answer:** It freezes the entire event loop; use run_in_executor or an async API

One slow call stalls everything.

### [03 · Metaprogramming](level-4/03-metaprogramming.md)

**Q133.** What does a metaclass hook do?

```python
class Meta(type):
    def __new__(m,n,b,d):
        d['registered']=True
        return super().__new__(m,n,b,d)
class A(metaclass=Meta): pass
print(A.registered, type(A).__name__)
```

**Answer:** True Meta

Metaclasses customise class creation. Verified by running it.

**Q134.** What does __init_subclass__ give you (a simpler hook)?

```python
registry=[]
class Base:
    def __init_subclass__(cls,**kw):
        super().__init_subclass__(**kw); registry.append(cls.__name__)
class A(Base): pass
class B(Base): pass
print(registry)
```

**Answer:** ['A', 'B']

Runs whenever a subclass is defined. Verified by running it.

**Q135.** What do getattr and dynamic attribute access allow?

```python
class Dyn:
    def __getattr__(s,n):
        if n.startswith('get_'): return lambda: n[4:]
        raise AttributeError(n)
d=Dyn()
print(d.get_name(), hasattr(d,'zzz'))
```

**Answer:** name False

__getattr__ runs only when normal lookup fails. Verified by running it.

**Q136.** What is the risk of metaprogramming?

**Answer:** Hard-to-read, hard-to-debug code; use it where it removes real duplication

Prefer decorators and plain code.

### [04 · Production-Grade APIs](level-4/04-production-apis.md)

**Q137.** What does a health-check style readiness function return?

```python
def ready(db_ok,cache_ok):
    status={'db':db_ok,'cache':cache_ok}
    return (200 if all(status.values()) else 503), status
print(ready(True,True), ready(True,False))
```

**Answer:** (200, {'db': True, 'cache': True}) (503, {'db': True, 'cache': False})

Readiness reflects dependencies so load balancers stop routing to unready instances. Verified by running it.

**Q138.** What does structured logging look like?

```python
import json,logging,io
buf=io.StringIO(); h=logging.StreamHandler(buf)
h.setFormatter(logging.Formatter('%(message)s'))
l=logging.getLogger('x'); l.addHandler(h); l.setLevel(logging.INFO)
l.info(json.dumps({'event':'order','id':7,'ms':12}))
print(json.loads(buf.getvalue())['id'])
```

**Answer:** 7

JSON log lines are machine-searchable. Verified by running it.

**Q139.** What belongs in production configuration?

**Answer:** Environment variables for secrets and settings, never hard-coded in source

Twelve-factor style.

**Q140.** Why add rate limiting and timeouts?

**Answer:** Protect the service from abuse and slow clients

Return 429 with Retry-After.

### [05 · Testing at Scale](level-4/05-testing-at-scale.md)

**Q141.** What does parametrised testing do?

```python
cases=[(1,1),(2,4),(3,9)]
def sq(n): return n*n
print(all(sq(a)==b for a,b in cases), len(cases))
```

**Answer:** True 3

One test body, many inputs. Verified by running it.

**Q142.** What does a fake (test double) enable?

```python
class FakeClock:
    def __init__(s): s.t=0
    def now(s): return s.t
    def advance(s,x): s.t+=x
def expired(c,start,ttl): return c.now()-start>=ttl
c=FakeClock()
print(expired(c,0,10)); c.advance(10); print(expired(c,0,10))
```

**Answer:** False
True

Controlling time makes time-based logic testable. Verified by running it.

**Q143.** What does property-based testing (Hypothesis) do?

**Answer:** Generates many inputs to check that a property always holds and shrinks failures

Finds edge cases.

**Q144.** How do you keep a large test suite fast?

**Answer:** Isolate units, parallelise (pytest-xdist), use fakes and keep slow tests separate

Tier the suite.

### [06 · Data Engineering](level-4/06-data-engineering.md)

**Q145.** What does this ETL step print?

```python
raw=[{'id':1,'amt':'10.5'},{'id':2,'amt':'x'},{'id':1,'amt':'10.5'},{'id':3,'amt':'7'}]
seen=set(); good=[]; bad=[]
for r in raw:
    try: v=float(r['amt'])
    except ValueError: bad.append(r['id']); continue
    if r['id'] in seen: continue
    seen.add(r['id']); good.append((r['id'],v))
print(good, bad, sum(v for _,v in good))
```

**Answer:** [(1, 10.5), (3, 7.0)] [2] 17.5

Validate, quarantine bad rows and deduplicate. Verified by running it.

**Q146.** What does chunked processing look like?

```python
def chunks(it,n):
    b=[]
    for x in it:
        b.append(x)
        if len(b)==n: yield b; b=[]
    if b: yield b
print([sum(c) for c in chunks(range(10),4)])
```

**Answer:** [6, 22, 17]

Process big data in bounded batches. Verified by running it.

**Q147.** What makes a pipeline idempotent?

**Answer:** Re-running it with the same input leaves the same result (upserts, overwrite partitions)

Safe retries.

**Q148.** Why validate data at the pipeline boundary?

**Answer:** Bad data is cheapest to catch before it spreads

Schema checks.

### [07 · ML Foundations](level-4/07-ml-foundations.md)

**Q149.** What does a train/test split protect against?

```python
import random
random.seed(1)
data=list(range(10)); random.shuffle(data)
train,test=data[:8],data[8:]
print(len(train),len(test),set(train)&set(test))
```

**Answer:** 8 2 set()

Evaluate on data the model has not seen. Verified by running it.

**Q150.** How do you compute accuracy and a confusion count?

```python
y=[1,0,1,1,0,0,1,0]; p=[1,0,0,1,0,1,1,0]
acc=sum(a==b for a,b in zip(y,p))/len(y)
tp=sum(a==1 and b==1 for a,b in zip(y,p)); fp=sum(a==0 and b==1 for a,b in zip(y,p)); fn=sum(a==1 and b==0 for a,b in zip(y,p))
print(acc,tp,fp,fn)
```

**Answer:** 0.75 3 1 1

Accuracy is the fraction correct; precision and recall use tp, fp, fn. Verified by running it.

**Q151.** What does a simple linear fit find?

```python
xs=[1,2,3,4]; ys=[2,4,6,8]
n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
print(b, my-b*mx)
```

**Answer:** 2.0 0.0

Least squares slope and intercept. Verified by running it.

**Q152.** What is overfitting?

**Answer:** A model memorises training data and performs worse on new data

Use validation data and regularisation.

### [08 · Deployment &amp; DevOps](level-4/08-deployment-devops.md)

**Q153.** Why containerise a Python service?

**Answer:** Package code and dependencies for identical runs across environments

Docker images.

**Q154.** What goes in a production Dockerfile for Python?

**Answer:** A slim base image, pinned dependencies, a non-root user and a clear command

Layer caching: copy requirements first.

**Q155.** What does a graceful shutdown handler do?

```python
import signal,os
flag={'stop':False}
signal.signal(signal.SIGTERM,lambda *a: flag.update(stop=True))
os.kill(os.getpid(),signal.SIGTERM)
print(flag['stop'])
```

**Answer:** True

Handle SIGTERM to finish in-flight work before exiting. Verified by running it.

**Q156.** What belongs in a CI pipeline for Python?

**Answer:** Lint, type-check, test with coverage, build the image and deploy on success

Automate everything.

### [09 · Security Best Practices](level-4/09-security-best-practices.md)

**Q157.** What does hashing a password correctly involve?

```python
import hashlib,os
salt=os.urandom(16)
h=hashlib.scrypt(b'pw',salt=salt,n=2**14,r=8,p=1)
h2=hashlib.scrypt(b'pw',salt=salt,n=2**14,r=8,p=1)
print(h==h2, len(h)==64, hashlib.scrypt(b'other',salt=salt,n=2**14,r=8,p=1)==h)
```

**Answer:** True True False

A salted, slow key-derivation function; compare with a constant-time check in real code. Verified by running it.

**Q158.** Why compare secrets with hmac.compare_digest?

```python
import hmac
print(hmac.compare_digest('abc','abc'), hmac.compare_digest('abc','abd'))
```

**Answer:** True False

It avoids timing leaks that early-exit comparisons have. Verified by running it.

**Q159.** What does parameterised input prevent?

```python
import sqlite3
c=sqlite3.connect(':memory:'); c.execute('create table u(n text)'); c.execute("insert into u values ('ana')")
evil="x' OR '1'='1"
bad=c.execute("select count(*) from u where n='"+evil+"'").fetchone()[0]
ok=c.execute('select count(*) from u where n=?',(evil,)).fetchone()[0]
print(bad,ok)
```

**Answer:** 1 0

String-built SQL was tricked into matching; the placeholder treated the input as data. Verified by running it.

**Q160.** Which is the safe way to load untrusted YAML or pickle data?

**Answer:** Use yaml.safe_load and avoid pickle for untrusted data (it can run code)

Never eval input.

### [10 · Capstone Project](level-4/10-capstone-project.md)

**Q161.** What does the capstone project demonstrate?

**Answer:** A complete, tested, documented application using the course's skills end to end

Design, build, test and ship.

**Q162.** What belongs in the README?

**Answer:** Purpose, setup, usage, design decisions and how to run tests

Others should run it in minutes.

**Q163.** What makes it production-ready?

**Answer:** Tests in CI, error handling, logging, configuration and a deployment path

Evidence over claims.

**Q164.** How do you handle residual risks?

**Answer:** Document them and decide to accept, mitigate or transfer

Record decisions.

## Mixed questions across all levels

**Q165.** What does this print?

```python
def f(x, acc=[]):
    acc.append(x)
    return acc
print(f(1), f(2), f(3, []))
```

**Answer:** [1, 2] [1, 2] [3]

A mutable default argument is created once and shared between calls; the first two results are the same list object. Verified by running it.

**Q166.** What does this comprehension and unpacking print?

```python
a,*mid,z=range(6)
d={k:v for k,v in zip('abc',[1,2,3]) if v!=2}
print(a,mid,z,d)
```

**Answer:** 0 [1, 2, 3, 4] 5 {'a': 1, 'c': 3}

Starred assignment collects the middle as a list. Verified by running it.

**Q167.** What does this late-binding closure print?

```python
fs=[lambda: i for i in range(3)]
gs=[lambda i=i: i for i in range(3)]
print([f() for f in fs],[g() for g in gs])
```

**Answer:** [2, 2, 2] [0, 1, 2]

Closures capture variables, not values; a default argument captures the value now. Verified by running it.

**Q168.** What does this generator pipeline print?

```python
def evens(it):
    for x in it:
        if x%2==0: yield x
def squares(it):
    for x in it: yield x*x
p=squares(evens(range(10)))
print(next(p), sum(p))
```

**Answer:** 0 120

Generators are lazy and consumed in order: next took 0 and sum took the remaining 4+16+36+64. Verified by running it.

**Q169.** What does this context manager print?

```python
from contextlib import contextmanager
out=[]
@contextmanager
def cm(n):
    out.append(f'enter {n}')
    try: yield
    finally: out.append(f'exit {n}')
with cm('a'), cm('b'):
    out.append('body')
print(out)
```

**Answer:** ['enter a', 'enter b', 'body', 'exit b', 'exit a']

Context managers exit in reverse order. Verified by running it.

**Q170.** What does this dataclass do with defaults?

```python
from dataclasses import dataclass, field
@dataclass
class Cart:
    items: list = field(default_factory=list)
a,b=Cart(),Cart()
a.items.append(1)
print(a.items,b.items)
```

**Answer:** [1] []

default_factory creates a fresh list per instance. Verified by running it.

**Q171.** What does this datetime/timezone code print?

```python
from datetime import datetime, timezone, timedelta
t=datetime(2026,3,5,23,30,tzinfo=timezone.utc)
local=t.astimezone(timezone(timedelta(hours=2)))
print(local.date(), local.hour, t.date())
```

**Answer:** 2026-03-06 1 2026-03-05

Converting zones can change the date. Verified by running it.

**Q172.** What does this asyncio code print?

```python
import asyncio
async def a(): await asyncio.sleep(0.02); return 'a'
async def b(): return 'b'
async def main():
    print(await asyncio.gather(a(),b()), await b())
asyncio.run(main())
```

**Answer:** ['a', 'b'] b

gather preserves the order of its arguments. Verified by running it.

**Q173.** What does a parameterised query avoid?

```python
import sqlite3
c=sqlite3.connect(':memory:'); c.execute('create table t(a)')
c.execute('insert into t values (?)',("x'); DROP TABLE t;--",))
print(c.execute('select count(*) from t').fetchone()[0])
```

**Answer:** 1

The malicious text was stored as data, not executed. Verified by running it.

**Q174.** When is multiprocessing a better fit than threading in CPython?

**Answer:** For CPU-bound work, because processes are not limited by the GIL

Threads suit I/O waits.

**Q175.** What does `if __name__ == '__main__':` do?

**Answer:** Runs the block only when the file is executed directly, not when imported

Keeps import side effects away.

**Q176.** Why prefer `with open(...)` to a bare open()?

**Answer:** The file is closed automatically even if an exception occurs

Context managers handle cleanup.

**Q177.** What is the difference between a list and a tuple?

**Answer:** Lists are mutable; tuples are immutable (and hashable if their items are)

Use tuples for fixed records.

**Q178.** Why use virtual environments?

**Answer:** Isolate each project's dependencies and versions

python -m venv .venv.

**Q179.** What does pytest discover by default?

**Answer:** Files named test_*.py and functions named test_*

Naming conventions matter.

**Q180.** What is the safest way to compare two floats in a test?

**Answer:** With a tolerance (math.isclose or pytest.approx)

Floating-point rounding.

**Q181.** What is a decorator?

**Answer:** A callable that takes a function and returns a replacement, applied with @

@d above def f is f = d(f).

**Q182.** What does EAFP mean?

**Answer:** Easier to ask forgiveness than permission: try the operation and handle the exception

Pythonic style.

**Q183.** What should you never do with untrusted input?

**Answer:** eval or exec it, or unpickle it

Arbitrary code execution.

**Q184.** Why measure before optimising?

**Answer:** The bottleneck is often not where you expect; profile first

cProfile and timeit.

## Practical coding questions

### A log analyser with regex, dataclasses and generators

Parse web-service log lines into immutable Entry objects with a regex with named groups, skipping garbage lines lazily with a generator, then report level counts, slowest paths, the server-error rate, affected users, the time window and the busiest minute using Counter, defaultdict and datetime.

Starter code:

```
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

Expected output:

```text
parsed 7 of 8 lines
levels: {'ERROR': 2, 'INFO': 4, 'WARN': 1}
slowest paths: [('/pay', 895), ('/items', 398)]
server error rate: 28.6%
users with errors: ['bo']
window: 0:02:29
busiest minute: ('10:00', 3)
```

??? success "Show a solution"

    ```
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

    PATTERN = re.compile(
        r"(?P<ts>\S+Z) (?P<level>[A-Z]+)\s+(?P<svc>\w+)\s+(?P<method>[A-Z]+) (?P<path>\S+) (?P<status>\d{3}) (?P<ms>\d+)ms user=(?P<user>\w+)"
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

    def parse(lines) -> Iterator[Entry]:
        for line in lines:
            m = PATTERN.match(line)
            if not m:
                continue
            g = m.groupdict()
            yield Entry(datetime.fromisoformat(g["ts"].replace("Z", "+00:00")), g["level"], g["svc"], g["method"], g["path"], int(g["status"]), int(g["ms"]), g["user"])

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

    A frozen dataclass gives a cheap, hashable record; the generator keeps parsing lazy and skips bad lines; Counter and defaultdict do the aggregation. The timestamp's trailing Z is replaced because fromisoformat needs an explicit offset on older Pythons. Verified by running the solution.

### An async job runner with retry decorator and bounded concurrency

Write an async retry decorator with exponential backoff (keeping the function name and counting retries), then run eight flaky jobs with a semaphore limiting concurrency to three. Job 7 never succeeds within three attempts and must be reported as failed without stopping the others.

Starter code:

```
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

Expected output:

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

??? success "Show a solution"

    ```
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

    random.seed(3)
    failures = {2: 2, 5: 1, 7: 9}   # job id -> how many times it fails before succeeding (7 never succeeds within 3 attempts)
    attempts_seen = {}

    @retry(attempts=3)
    async def fetch(job_id):
        attempts_seen[job_id] = attempts_seen.get(job_id, 0) + 1
        await asyncio.sleep(0.01)
        if attempts_seen[job_id] <= failures.get(job_id, 0):
            raise ConnectionError(f"job {job_id} flaky")
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
                    results[i] = ("ok", await fetch(i))
                except ConnectionError as e:
                    results[i] = ("failed", str(e))
                finally:
                    running -= 1
        t = time.perf_counter()
        await asyncio.gather(*(worker(i) for i in ids))
        return results, peak, time.perf_counter() - t

    results, peak, elapsed = asyncio.run(run(range(1, 9), limit=3))
    for i in sorted(results):
        print(i, *results[i])
    print("peak concurrency:", peak)
    print("retries performed:", fetch.retries)
    print("finished fast enough:", elapsed < 1.0)
    print("attempts per job:", dict(sorted(attempts_seen.items())))
    ```

    The decorator re-raises on the final attempt, the semaphore bounds concurrency and each worker converts the final failure into a result instead of letting gather abort. Retries total 5 (2 + 1 + 2). Verified by running the solution (timings are tiny sleeps; only deterministic facts are printed).

### Your first script

Write a script that stores your name in a variable and prints a greeting using an f-string.

Starter code:

```
name = "Asha"
# print the greeting here
```

Expected output:

```text
Hello, Asha! Welcome to Python.
```

??? success "Show a solution"

    ```
    name = "Asha"
    print(f"Hello, {name}! Welcome to Python.")
    ```

    An f-string (prefix f) evaluates expressions inside {} and inserts their values into the text.

### Temperature converter

Convert 100 degrees Celsius to Fahrenheit (F = C × 9/5 + 32) and print the result with one decimal place.

Starter code:

```
celsius = 100
# compute fahrenheit and print it
```

Expected output:

```text
100°C = 212.0°F
```

??? success "Show a solution"

    ```
    celsius = 100
    fahrenheit = celsius * 9 / 5 + 32
    print(f"{celsius}°C = {fahrenheit:.1f}°F")
    ```

    Division makes the result a float; the format spec :.1f prints exactly one decimal place.

### FizzBuzz to 15

Print the numbers 1 to 15, but print Fizz for multiples of 3, Buzz for multiples of 5 and FizzBuzz for multiples of both, all on one line separated by spaces.

Starter code:

```
results = []
for n in range(1, 16):
    # append the right value
    pass
print(" ".join(results))
```

Expected output:

```text
1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz
```

??? success "Show a solution"

    ```
    results = []
    for n in range(1, 16):
        if n % 15 == 0:
            results.append("FizzBuzz")
        elif n % 3 == 0:
            results.append("Fizz")
        elif n % 5 == 0:
            results.append("Buzz")
        else:
            results.append(str(n))
    print(" ".join(results))
    ```

    Check the combined case (divisible by 15) first, otherwise the Fizz branch would catch 15 before FizzBuzz.

### A reusable function

Write a function average(numbers) that returns the mean of a list, or 0 for an empty list. Print the results for [4, 8, 6] and [].

Starter code:

```
def average(numbers):
    # return the mean, or 0 for an empty list
    pass

print(average([4, 8, 6]))
print(average([]))
```

Expected output:

```text
6.0
0
```

??? success "Show a solution"

    ```
    def average(numbers):
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)

    print(average([4, 8, 6]))
    print(average([]))
    ```

    Guarding the empty case avoids ZeroDivisionError; sum()/len() returns a float.

### Word counter

Count how many times each word appears in the sentence and print the dictionary.

Starter code:

```
sentence = "the cat and the hat"
counts = {}
# fill counts
print(counts)
```

Expected output:

```text
{'the': 2, 'cat': 1, 'and': 1, 'hat': 1}
```

??? success "Show a solution"

    ```
    sentence = "the cat and the hat"
    counts = {}
    for word in sentence.split():
        counts[word] = counts.get(word, 0) + 1
    print(counts)
    ```

    dict.get(word, 0) starts each new word at 0. Dictionaries keep insertion order, so words print in the order first seen.

### Receipt line

Print an item name left-aligned in 10 characters and its price right-aligned with two decimals in 8 characters.

Starter code:

```
item = "Tea"
price = 20
# print one aligned receipt line
```

Expected output:

```text
Tea          20.00
```

??? success "Show a solution"

    ```
    item = "Tea"
    price = 20
    print(f"{item:<10}{price:>8.2f}")
    ```

    In a format spec, &lt; aligns left and &gt; aligns right within the given width; .2f adds two decimals.

### Write and read back

Write three lines to tasks.txt, then read the file and print how many lines it has.

Starter code:

```
tasks = ["buy milk", "call mom", "study python"]
# write the tasks, then count the lines
```

Expected output:

```text
3 lines
```

??? success "Show a solution"

    ```
    tasks = ["buy milk", "call mom", "study python"]
    with open("tasks.txt", "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(t + "\n")
    with open("tasks.txt", encoding="utf-8") as f:
        count = sum(1 for _ in f)
    print(f"{count} lines")
    ```

    Each write adds a newline, so the file has three lines; iterating the file counts them without loading it all at once.

### Safe number input

Write a function to_number(text) that returns the integer value, or None if the text is not a valid number. Print the results for "42" and "forty".

Starter code:

```
def to_number(text):
    # return int(text), or None on failure
    pass

print(to_number("42"))
print(to_number("forty"))
```

Expected output:

```text
42
None
```

??? success "Show a solution"

    ```
    def to_number(text):
        try:
            return int(text)
        except ValueError:
            return None

    print(to_number("42"))
    print(to_number("forty"))
    ```

    Catching only ValueError handles bad input while letting unexpected errors surface.

### Use the standard library

Use the statistics module to print the mean and median of the scores.

Starter code:

```
import statistics
scores = [70, 85, 90, 65, 85]
# print mean and median
```

Expected output:

```text
mean=79 median=85
```

??? success "Show a solution"

    ```
    import statistics
    scores = [70, 85, 90, 65, 85]
    print(f"mean={statistics.mean(scores)} median={statistics.median(scores)}")
    ```

    The standard library ships ready-made tools; statistics.mean and statistics.median avoid writing the maths yourself.

---

More free practice: the [Python Mastery Path](index.md) curriculum, the [Interview Prep Pack](https://learnmasterypath.com/interview-pack/) and the [free resume ATS check](https://learnmasterypath.com/resume/).
