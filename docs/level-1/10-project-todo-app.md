# 10 · Project — CLI To-Do App

A small end-to-end project combining everything from Level 1: functions, data
structures, strings, file I/O, error handling, and modules.

## What you'll build

A command-line to-do list that:

- Adds tasks
- Lists tasks (with done/pending status)
- Marks tasks done
- Deletes tasks
- Persists everything to a JSON file between runs

## Project layout

```text
todo_app/
    storage.py
    todo.py
```

## storage.py — persistence layer

```python
# storage.py
import json
from pathlib import Path

DB_PATH = Path("tasks.json")


def load_tasks() -> list[dict]:
    if not DB_PATH.exists():
        return []
    try:
        return json.loads(DB_PATH.read_text())
    except json.JSONDecodeError:
        return []


def save_tasks(tasks: list[dict]) -> None:
    DB_PATH.write_text(json.dumps(tasks, indent=2))
```

## todo.py — CLI logic

```python
# todo.py
import sys
from storage import load_tasks, save_tasks


def add_task(tasks, description):
    tasks.append({"description": description, "done": False})
    save_tasks(tasks)
    print(f"Added: {description}")


def list_tasks(tasks):
    if not tasks:
        print("No tasks yet.")
        return
    for i, task in enumerate(tasks, start=1):
        status = "x" if task["done"] else " "
        print(f"[{status}] {i}. {task['description']}")


def complete_task(tasks, index):
    try:
        tasks[index - 1]["done"] = True
        save_tasks(tasks)
        print(f"Marked task {index} done.")
    except IndexError:
        print(f"No task with number {index}")


def delete_task(tasks, index):
    try:
        removed = tasks.pop(index - 1)
        save_tasks(tasks)
        print(f"Deleted: {removed['description']}")
    except IndexError:
        print(f"No task with number {index}")


def main():
    tasks = load_tasks()
    args = sys.argv[1:]

    if not args:
        print("Usage: todo.py [add <text> | list | done <n> | delete <n>]")
        return

    command = args[0]

    if command == "add" and len(args) > 1:
        add_task(tasks, " ".join(args[1:]))
    elif command == "list":
        list_tasks(tasks)
    elif command == "done" and len(args) > 1:
        complete_task(tasks, int(args[1]))
    elif command == "delete" and len(args) > 1:
        delete_task(tasks, int(args[1]))
    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
```

## Running it

```bash
python3 todo.py add "Write Level 1 exercises"
python3 todo.py add "Review Level 2 outline"
python3 todo.py list
# [ ] 1. Write Level 1 exercises
# [ ] 2. Review Level 2 outline

python3 todo.py done 1
python3 todo.py list
# [x] 1. Write Level 1 exercises
# [ ] 2. Review Level 2 outline
```

## Stretch goals

- Add due dates and sort tasks by them.
- Add a `priority` field (`low`/`medium`/`high`) and color the output using
  ANSI codes.
- Add unit tests for `storage.py` (you'll formalize this properly with `pytest`
  in [Level 2](../level-2/09-testing-basics.md)).

Completing this project means you're ready for **Level 2 · Intermediate**.
