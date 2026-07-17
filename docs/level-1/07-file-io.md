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

## Exercise

Write a script that reads a text file, counts how many times each word
appears (case-insensitive), and writes the results as `word,count` lines to a
new file, sorted by count descending.
