---
title: "Final Quiz"
description: "Test what you have learned across all four levels of Python Mastery Path with a 10-question final quiz."
---

# Final Quiz

Ten questions drawn from all four levels of this course. You need **70% (7 out of 10)** to pass
and unlock your course completion certificate — you can retake it as many times as you like.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "level": 1,
    "topic": "Setup & First Program",
    "question": "A Python file defines a function and ends with `if __name__ == \"__main__\": main()`. What is the actual purpose of this guard?",
    "options": [
      "It improves the script's startup performance by skipping unused code.",
      "It lets the file's functions be imported by other modules without automatically re-running that file's top-level script logic.",
      "It is required by Python's syntax for every script that defines functions.",
      "It tells the interpreter to compile the file to bytecode instead of running it directly."
    ],
    "correctIndex": 1,
    "explanation": "When a file is run directly, CPython sets its module's __name__ to \"__main__\"; when the same file is imported, __name__ is instead the module's own name. The guard uses this to run script-only logic (like calling main()) only in the first case."
  },
  {
    "level": 1,
    "topic": "Variables, Data Types & Operators",
    "question": "What is the fundamental difference between Python's `==` and `is` operators?",
    "options": [
      "`==` compares object identity (same memory address); `is` compares value equality.",
      "`is` compares object identity (same memory address); `==` compares value equality via `__eq__`.",
      "They are interchangeable for all built-in types, differing only in style.",
      "`is` is deprecated in modern Python in favor of `==` for all comparisons."
    ],
    "correctIndex": 1,
    "explanation": "`is` asks whether two names point to the exact same object in memory (comparing pointers); `==` asks whether two objects represent the same value, by calling the left operand's __eq__ method."
  },
  {
    "level": 1,
    "topic": "Modules, Packages & pip",
    "question": "A module's top-level code runs only once per process, no matter how many times it's imported from different places in a program. What mechanism makes this true?",
    "options": [
      "Python caches every imported module in `sys.modules`, and a later import of the same name returns the cached module object instead of re-running its code.",
      "The `import` statement only works the first time it's called; subsequent calls silently fail.",
      "Python detects duplicate `import` statements at compile time and removes them.",
      "Each module is automatically compiled into a singleton class by the interpreter."
    ],
    "correctIndex": 0,
    "explanation": "Python checks sys.modules first; a cache hit returns the existing module object immediately. This is also why circular imports between two modules don't loop forever \u2014 the second import finds the (possibly still-partial) module already registered in the cache."
  },
  {
    "level": 2,
    "topic": "Comprehensions & Generators",
    "question": "Why would `sum(n * n for n in range(1_000_000))` generally be preferred over `sum([n * n for n in range(1_000_000)])`?",
    "options": [
      "The generator expression version produces a slightly different, more numerically precise sum due to lazy evaluation.",
      "The list comprehension version would raise a `MemoryError` on most machines for a range this large.",
      "The generator expression produces values one at a time without ever building the full intermediate list in memory, while the list comprehension allocates the entire list first.",
      "`sum()` raises a `TypeError` if given a list instead of a generator."
    ],
    "correctIndex": 2,
    "explanation": "A generator expression is lazy \u2014 it yields one value at a time on demand, so sum() can consume and discard each value immediately. The list comprehension form builds the entire 1,000,000-element list in memory before sum() even starts adding anything up."
  },
  {
    "level": 2,
    "topic": "Functional Programming",
    "question": "`make_multiplier(2)` and `make_multiplier(3)` each return an inner function that remembers a different `factor`. What does this reveal about how Python closures actually work?",
    "options": [
      "Each inner function copies the value of `factor` into its own private variable at the moment it's defined.",
      "Closures only work correctly with integer arguments, not other types.",
      "Each call to the outer function creates its own separate cell object holding `factor`, and the inner function stores a reference to that specific cell \u2014 so different calls close over genuinely different cells, not shared or copied values.",
      "Python reparses and recompiles the inner function's source code each time the outer function is called."
    ],
    "correctIndex": 2,
    "explanation": "The compiler treats a variable read by a nested function as a 'cell variable' \u2014 a small box object \u2014 rather than a normal local. Each call to the outer function creates a fresh cell; the closure captures a reference to that cell, not a copied value, which is also the mechanism behind the classic 'late binding' gotcha."
  },
  {
    "level": 3,
    "topic": "Concurrency I \u2014 Threading & Multiprocessing",
    "question": "Four Python threads each run a tight, pure-Python CPU-bound loop (`count += 1`) on a 4-core machine. Why does this not run roughly 4x faster than a single thread?",
    "options": [
      "Python threads are cooperatively scheduled only at explicit I/O points, so a CPU-bound loop with no I/O never yields control to other threads at all.",
      "CPython's Global Interpreter Lock (GIL) allows only one thread to execute Python bytecode at a time, so the threads take turns rather than truly running in parallel.",
      "The `threading` module silently falls back to running threads sequentially whenever it detects CPU-bound work.",
      "The operating system's scheduler chose not to assign the threads to separate cores, which Python has no way to influence."
    ],
    "correctIndex": 1,
    "explanation": "The GIL exists because CPython's reference-counting memory management isn't thread-safe without it. It's released during blocking I/O (which is why threading helps I/O-bound work), but held continuously by whichever thread is executing pure Python bytecode \u2014 so CPU-bound threads just take turns on one core, not run in parallel."
  },
  {
    "level": 3,
    "topic": "Advanced Decorators & Descriptors",
    "question": "A decorator wraps a function in an inner `wrapper(*args, **kwargs)` function. Without using `functools.wraps`, what breaks?",
    "options": [
      "The decorated function stops working correctly at runtime and raises an exception.",
      "The wrapper function replaces the original's identity \u2014 `__name__`, `__doc__`, and introspection tools see the wrapper's metadata instead of the original function's.",
      "Python refuses to apply the decorator at import time.",
      "The decorated function can no longer accept any arguments."
    ],
    "correctIndex": 1,
    "explanation": "A decorator's wrapper is a brand-new function object with its own __name__ ('wrapper') and __doc__ (None). functools.wraps copies the original function's __name__, __doc__, and related attributes onto the wrapper after the fact, fixing debugging and introspection \u2014 it doesn't change runtime behavior otherwise."
  },
  {
    "level": 3,
    "topic": "Databases (SQLite & SQLAlchemy)",
    "question": "Why do parameterized queries (`cursor.execute(\"... WHERE name = ?\", (name,))`) prevent SQL injection, while an f-string-built query doesn't?",
    "options": [
      "Parameterized queries automatically strip all special characters from the input before running it.",
      "The database driver sends the SQL text and the value through separate channels \u2014 the value is bound into an already-parsed query structure and is never re-parsed as SQL syntax, unlike text spliced into an f-string before parsing.",
      "f-strings execute more slowly, which gives attackers less practical opportunity to exploit the query.",
      "Parameterized queries only work with SELECT statements, so injection on INSERT/UPDATE is not a risk."
    ],
    "correctIndex": 1,
    "explanation": "SQLite (and most databases) compile a parameterized query's structure once, with a placeholder hole, then bind the value directly into that hole as data \u2014 it never becomes part of the SQL grammar. An f-string instead splices untrusted text directly into the SQL before parsing, so a value like ' OR '1'='1 becomes part of the query's syntax instead of staying a data value."
  },
  {
    "level": 4,
    "topic": "Security Best Practices",
    "question": "Why is `pickle.loads()` considered dangerous on untrusted data, while `json.loads()` is safe for the same purpose?",
    "options": [
      "Pickle files are always larger, making them slower to process and more prone to corruption.",
      "`json.loads()` encrypts the data automatically, while `pickle.loads()` does not.",
      "A pickle stream can include instructions that call arbitrary callables during deserialization to reconstruct objects, so unpickling can execute attacker-controlled code; JSON's format has no equivalent instruction and can only produce plain data types.",
      "`pickle` only works correctly under Python 2, so using it on modern systems is inherently unstable."
    ],
    "correctIndex": 2,
    "explanation": "Pickle's format is effectively a small bytecode program that reconstructs arbitrary objects, including by calling named callables \u2014 that's by design, since it's how custom __reduce__ objects get rebuilt. JSON's grammar can only ever build dicts, lists, strings, numbers, booleans, and null \u2014 there is no opcode in the format for 'call this function.'"
  },
  {
    "level": 4,
    "topic": "ML Foundations",
    "question": "When preparing data for a model, why should `StandardScaler` be `fit` only on the training set, then used to `transform` both the training and test sets \u2014 never `fit` on the test set too?",
    "options": [
      "Fitting on the test set would make the code noticeably slower to run.",
      "Fitting on the test set (even just for scaling) lets information about the test data's distribution leak into preprocessing, producing an optimistic, unrealistic performance estimate that won't hold on genuinely new data.",
      "`StandardScaler` can only be fit once per Python process, regardless of which data is used.",
      "Scikit-learn raises an error if you attempt to fit a scaler more than once."
    ],
    "correctIndex": 1,
    "explanation": "fit() computes and stores the mean/std from whatever data it's given. If the test set contributes to that calculation, the model effectively gets a sneak peek at test-set statistics before evaluation \u2014 an optimistic bias that won't reproduce in production on data the model has truly never seen."
  }
]
</script>
