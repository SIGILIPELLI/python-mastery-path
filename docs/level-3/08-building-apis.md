# 08 · Building APIs (Flask/FastAPI)

So far you've been a client of other people's APIs. This module flips that:
building your own web API with **FastAPI**, a modern framework built on type
hints, automatic request validation via Pydantic, and automatically generated
interactive documentation.

## Installing FastAPI

```bash
pip install fastapi uvicorn
```

`uvicorn` is the ASGI server that actually runs a FastAPI application.

## A minimal API

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="Task API")


@app.get("/")
def root():
    return {"message": "Task API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```bash
uvicorn main:app --reload
# visit http://127.0.0.1:8000/         -> {"message": "Task API is running"}
# visit http://127.0.0.1:8000/docs     -> interactive Swagger UI, generated automatically
```

## Path and query parameters

FastAPI reads Python type hints to validate and convert incoming data
automatically.

```python
from fastapi import FastAPI

app = FastAPI()

tasks = {1: "Write docs", 2: "Review PR"}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):          # FastAPI converts the URL segment to int, or 422s
    return {"task_id": task_id, "title": tasks.get(task_id)}


@app.get("/tasks")
def list_tasks(limit: int = 10, done: bool | None = None):
    # limit and done are optional query params: /tasks?limit=5&done=true
    return {"limit": limit, "done_filter": done}
```

Visiting `/tasks/abc` (a non-integer) automatically returns a `422 Unprocessable
Entity` response with a clear validation error — no manual checking required.

## Request bodies with Pydantic models

Pydantic models define the *shape* of data you expect, and FastAPI validates
incoming JSON against them automatically.

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool


tasks_db: dict[int, TaskOut] = {}
next_id = 1


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = TaskOut(id=next_id, title=task.title, done=task.done)
    tasks_db[next_id] = new_task
    next_id += 1
    return new_task
```

If the client sends `{"title": ""}` (violating `min_length=1`), FastAPI
rejects it with a `422` response describing exactly which field failed and
why — before your function body ever runs.

## Full CRUD example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API")


class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool


tasks_db: dict[int, TaskOut] = {}
next_id = 1


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = TaskOut(id=next_id, **task.model_dump())
    tasks_db[next_id] = new_task
    next_id += 1
    return new_task


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks():
    return list(tasks_db.values())


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    task = tasks_db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, patch: TaskUpdate):
    task = tasks_db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    updated_data = task.model_dump()
    updated_data.update({k: v for k, v in patch.model_dump().items() if v is not None})
    updated_task = TaskOut(**updated_data)
    tasks_db[task_id] = updated_task
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="task not found")
    del tasks_db[task_id]
```

`HTTPException` is FastAPI's way of returning a specific HTTP status code and
error body from inside a route — raising it works like any other exception,
but FastAPI catches it and turns it into the right response.

## Dependency injection

FastAPI's `Depends` lets you share setup logic (like "get the current user" or
"get a database session") across multiple routes cleanly.

```python
from fastapi import Depends, FastAPI

app = FastAPI()


def get_query_token(token: str | None = None):
    if token != "secret-token":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="invalid or missing token")
    return token


@app.get("/protected")
def protected_route(token: str = Depends(get_query_token)):
    return {"message": "you're in", "token": token}
```

## Testing a FastAPI app

FastAPI's own `TestClient` makes it easy to exercise routes without running a
real server.

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_and_get_task():
    response = client.post("/tasks", json={"title": "Test task"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test task"


def test_get_missing_task_returns_404():
    response = client.get("/tasks/9999")
    assert response.status_code == 404
```

## Cheat sheet

| Concept | Syntax |
|---------|--------|
| Path parameter | `def route(item_id: int):` with `@app.get("/items/{item_id}")` |
| Query parameter | plain function argument with a default value |
| Request body | a `BaseModel` subclass as a function argument |
| Response shape | `response_model=` on the route decorator |
| Error response | `raise HTTPException(status_code=..., detail=...)` |
| Shared logic | `Depends(dependency_function)` |

## Exercise

Extend the CRUD example above with a `priority: str` field on `TaskCreate`
(one of `"low"`, `"medium"`, `"high"`, validated with a Pydantic
`Field`/`Literal`), a `GET /tasks?priority=high` filter using a query
parameter, and a `TestClient`-based test file covering create, list-with-filter,
update, and delete-then-404.
