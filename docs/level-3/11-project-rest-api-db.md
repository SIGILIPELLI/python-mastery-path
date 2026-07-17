# 11 · Project — REST API + Database

The Level 3 capstone: a complete FastAPI service backed by a real SQLite
database via SQLAlchemy, with full CRUD, Pydantic validation, proper error
handling, and a `pytest` test suite that exercises the whole stack.

## What you'll build

A "Book Catalog" API that:

- Persists books to a SQLite database using the SQLAlchemy ORM
- Exposes `POST`, `GET` (list + single), `PATCH`, and `DELETE` endpoints
- Validates input with Pydantic models, separate from the database models
- Returns proper HTTP status codes and error bodies for missing/invalid data
- Has an isolated, file-independent test suite using an in-memory database

## Project layout

```text
book_api/
    app/
        __init__.py
        database.py
        models.py
        schemas.py
        crud.py
        main.py
    tests/
        conftest.py
        test_books.py
    requirements.txt
```

## requirements.txt

```text
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
pytest==8.2.0
httpx==0.27.0
```

## app/database.py — engine & session setup

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./books.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a session, always closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## app/models.py — the database table

```python
# app/models.py
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(200))
    year: Mapped[int] = mapped_column(Integer)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
```

## app/schemas.py — Pydantic request/response models

```python
# app/schemas.py
from pydantic import BaseModel, Field, ConfigDict


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=200)
    year: int = Field(ge=0, le=2100)
    read: bool = False


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=0, le=2100)
    read: bool | None = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # allows building this from an ORM object

    id: int
    title: str
    author: str
    year: int
    read: bool
```

Keeping `schemas.py` (API shape) separate from `models.py` (database shape) is
deliberate: it lets the API contract evolve independently of the storage
layer, and it means internal-only columns never leak into a response by
accident.

## app/crud.py — database operations

```python
# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from . import models, schemas


def create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_book(db: Session, book_id: int) -> models.Book | None:
    return db.get(models.Book, book_id)


def list_books(db: Session, read: bool | None = None) -> list[models.Book]:
    stmt = select(models.Book)
    if read is not None:
        stmt = stmt.where(models.Book.read == read)
    return list(db.scalars(stmt))


def update_book(db: Session, book_id: int, patch: schemas.BookUpdate) -> models.Book | None:
    db_book = get_book(db, book_id)
    if db_book is None:
        return None
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int) -> bool:
    db_book = get_book(db, book_id)
    if db_book is None:
        return False
    db.delete(db_book)
    db.commit()
    return True
```

`exclude_unset=True` in `update_book` means a `PATCH` only overwrites fields
the client actually sent — `None` in the request stays untouched rather than
wiping out an existing value.

## app/main.py — the FastAPI app

```python
# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Book Catalog API")


@app.post("/books", response_model=schemas.BookOut, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, book)


@app.get("/books", response_model=list[schemas.BookOut])
def list_books(read: bool | None = None, db: Session = Depends(get_db)):
    return crud.list_books(db, read=read)


@app.get("/books/{book_id}", response_model=schemas.BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="book not found")
    return book


@app.patch("/books/{book_id}", response_model=schemas.BookOut)
def update_book(book_id: int, patch: schemas.BookUpdate, db: Session = Depends(get_db)):
    book = crud.update_book(db, book_id, patch)
    if book is None:
        raise HTTPException(status_code=404, detail="book not found")
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_book(db, book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="book not found")
```

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# visit http://127.0.0.1:8000/docs for interactive Swagger UI
```

```bash
curl -X POST http://127.0.0.1:8000/books \
    -H "Content-Type: application/json" \
    -d '{"title": "Clean Code", "author": "Robert Martin", "year": 2008}'

curl http://127.0.0.1:8000/books
curl http://127.0.0.1:8000/books?read=false
```

## tests/conftest.py — an isolated test database

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def client():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

Overriding the `get_db` dependency with an in-memory SQLite database means
every test run starts from a clean slate and never touches the real
`books.db` file.

## tests/test_books.py

```python
# tests/test_books.py

def test_create_book(client):
    response = client.post("/books", json={"title": "Dune", "author": "Frank Herbert", "year": 1965})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Dune"
    assert body["read"] is False
    assert "id" in body


def test_create_book_rejects_invalid_year(client):
    response = client.post("/books", json={"title": "Bad Book", "author": "Nobody", "year": 9999})
    assert response.status_code == 422


def test_get_book_not_found(client):
    response = client.get("/books/999")
    assert response.status_code == 404


def test_list_and_filter_books(client):
    client.post("/books", json={"title": "Book A", "author": "X", "year": 2000, "read": True})
    client.post("/books", json={"title": "Book B", "author": "Y", "year": 2010, "read": False})

    all_books = client.get("/books").json()
    assert len(all_books) == 2

    unread = client.get("/books?read=false").json()
    assert len(unread) == 1
    assert unread[0]["title"] == "Book B"


def test_update_book_partial(client):
    created = client.post("/books", json={"title": "WIP", "author": "Someone", "year": 2020}).json()

    response = client.patch(f"/books/{created['id']}", json={"read": True})
    assert response.status_code == 200
    updated = response.json()
    assert updated["read"] is True
    assert updated["title"] == "WIP"   # untouched fields stay the same


def test_delete_book(client):
    created = client.post("/books", json={"title": "Temp", "author": "Someone", "year": 2020}).json()

    delete_response = client.delete(f"/books/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/books/{created['id']}")
    assert get_response.status_code == 404
```

## Running the tests

```bash
pytest -v tests/
# tests/test_books.py::test_create_book PASSED
# tests/test_books.py::test_create_book_rejects_invalid_year PASSED
# tests/test_books.py::test_get_book_not_found PASSED
# tests/test_books.py::test_list_and_filter_books PASSED
# tests/test_books.py::test_update_book_partial PASSED
# tests/test_books.py::test_delete_book PASSED
```

## Stretch goals

- Add pagination (`?limit=&offset=`) to `GET /books`.
- Add a `genre` field with an enum-constrained value in the Pydantic schema.
- Package the app (tying back to
  [Packaging & Distribution](09-packaging-distribution.md)) with a console
  script that starts the server.

Completing this project means you're ready for **Level 4 · Master**.
