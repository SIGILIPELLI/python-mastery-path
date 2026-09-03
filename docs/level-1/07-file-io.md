# 07 · File I/O Basics

## Writing and reading text files

Always use `with` — it guarantees the file is closed even if an error occurs.

```python
with open("notes.txt", "w") as f:
    f.write("first line\n")
    f.write("second line\n")

with open("notes.txt", "r") as f:
    contents = f.read()
    print(contents)
```

## Reading line by line

```python
with open("notes.txt", "r") as f:
    for line in f:
        print(line.strip())
```

## Append mode

```python
with open("notes.txt", "a") as f:
    f.write("third line\n")
```

## File modes cheat sheet

| Mode | Meaning |
|------|---------|
| `"r"` | read (default, error if file missing) |
| `"w"` | write (creates file, **overwrites** existing content) |
| `"a"` | append (creates file if missing, adds to the end) |
| `"x"` | exclusive create (errors if file already exists) |
| `"rb"` / `"wb"` | binary read/write |

## Working with paths (prefer `pathlib` over string paths)

```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

file_path = data_dir / "notes.txt"
file_path.write_text("hello\n")
print(file_path.read_text())
print(file_path.exists())
```

## How It Actually Works

`open()` doesn't read anything — it asks the operating system for a **file
descriptor** (a small integer the kernel uses to track the open file), then
wraps that descriptor in a stack of Python objects:

1. **`FileIO`** — the raw layer. It translates `.read()`/`.write()` into the
   `read(2)`/`write(2)` system calls on the descriptor. System calls are
   relatively expensive (a switch into the kernel), so you don't want one per
   character.
2. **`BufferedReader`/`BufferedWriter`** — an in-memory buffer (8 KB by
   default). Reads pull a big chunk from the OS and hand you slices of it;
   writes accumulate in the buffer and flush to the OS only when it fills, when
   you call `.flush()`, or when the file closes. This is why data you "wrote"
   can be missing from the file until close.
3. **`TextIOWrapper`** — only for text mode. It decodes incoming bytes to `str`
   using the specified (or locale-default) encoding, encodes outgoing `str`
   back to bytes, and does newline translation (`\r\n` ↔ `\n` on Windows).
   `newline=""` for `csv` disables that translation.

**`with open(...) as f:`** compiles to: call `open()`, call its `__enter__`
(which returns the file object itself), run the body, then *guaranteed* call
`f.__exit__()` — even on an exception or `return` — which calls `.close()`.
`close()` flushes the buffer and then calls `close(2)` to release the
descriptor back to the kernel. Descriptors are a limited per-process resource,
so leaking them (never closing) eventually raises "Too many open files".
`pathlib.Path.read_text()` is a convenience that does the whole
open → read → close cycle in one call.

## Exercise

Write a script that reads a text file, counts how many times each word
appears (case-insensitive), and writes the results as `word,count` lines to a
new file, sorted by count descending.
