# 06 · Databases (SQLite & SQLAlchemy)

Most applications need to persist structured data beyond a single run. This
module covers `sqlite3` — a full SQL database built into the standard
library, requiring no server — and then SQLAlchemy, the most widely used ORM
(Object-Relational Mapper) in the Python ecosystem, which lets you work with
rows as Python objects instead of writing raw SQL everywhere.

## `sqlite3` — connecting and creating tables

```python
import sqlite3

connection = sqlite3.connect("app.db")   # creates the file if it doesn't exist
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
""")
connection.commit()
```

## Inserting data — always use parameters

```python
cursor.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ("Ada Lovelace", "ada@example.com"),
)
connection.commit()
print(cursor.lastrowid)   # the auto-generated id of the row just inserted

# inserting many rows at once
people = [("Grace Hopper", "grace@example.com"), ("Alan Turing", "alan@example.com")]
cursor.executemany("INSERT INTO users (name, email) VALUES (?, ?)", people)
connection.commit()
```

Never build SQL with an f-string or `%`-formatting when values come from user
input — always use `?` placeholders, which `sqlite3` escapes safely and which
protect you from SQL injection.

```python
# NEVER do this with untrusted input:
# cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")   # SQL injection risk

# always do this instead:
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
```

## Querying data

```python
cursor.execute("SELECT id, name, email FROM users WHERE name LIKE ?", ("%Ada%",))
row = cursor.fetchone()
print(row)   # (1, 'Ada Lovelace', 'ada@example.com') — a plain tuple by default

cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)
```

## Getting dict-like rows

```python
connection.row_factory = sqlite3.Row   # rows behave like dicts AND tuples
cursor = connection.cursor()

cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row["name"], row["email"])
```

## Using `sqlite3` as a context manager

The connection object supports `with`, which commits automatically on success
or rolls back on an exception — but note it does **not** close the connection.

```python
with connection:
    connection.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("Margaret Hamilton", "margaret@example.com"),
    )
# committed automatically here (or rolled back if an exception was raised)

connection.close()
```

## SQLAlchemy — the ORM approach

Writing raw SQL for every operation gets repetitive and error-prone as an
application grows. SQLAlchemy's ORM lets you define Python classes that map to
database tables, and work with rows as objects.

```bash
pip install sqlalchemy
```

```python
from sqlalchemy import create_engine, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)

    def __repr__(self):
        return f"User(id={self.id}, name={self.name!r})"


engine = create_engine("sqlite:///app_orm.db")
Base.metadata.create_all(engine)   # creates tables from the model classes
```

## CRUD with SQLAlchemy sessions

```python
with Session(engine) as session:
    # Create
    new_user = User(name="Katherine Johnson", email="katherine@example.com")
    session.add(new_user)
    session.commit()

    # Read
    from sqlalchemy import select
    stmt = select(User).where(User.name.like("%Johnson%"))
    for user in session.scalars(stmt):
        print(user)

    # Update
    user = session.scalars(select(User).where(User.email == "katherine@example.com")).first()
    user.name = "Katherine G. Johnson"
    session.commit()

    # Delete
    session.delete(user)
    session.commit()
```

## Relationships between tables

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[List["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="books")


with Session(engine) as session:
    author = Author(name="Robert Martin", books=[Book(title="Clean Code")])
    session.add(author)
    session.commit()

    fetched = session.scalars(select(Author).where(Author.name == "Robert Martin")).first()
    for book in fetched.books:
        print(book.title)
```

## A short intro to migrations

As your models change over time (new columns, renamed tables), you need a
controlled way to evolve the actual database schema without losing data —
that's what a migration tool provides. **Alembic** is SQLAlchemy's standard
migration tool.

```bash
pip install alembic
alembic init migrations              # scaffolds a migrations/ folder + alembic.ini
alembic revision --autogenerate -m "create users table"   # diff models vs. DB, generate a migration script
alembic upgrade head                  # apply all pending migrations
alembic downgrade -1                  # roll back the most recent migration
```

Each migration script has an `upgrade()` and `downgrade()` function, so schema
changes are tracked, reversible, and repeatable across environments.

## `sqlite3` vs. SQLAlchemy

| | `sqlite3` (stdlib) | SQLAlchemy |
|---|---|---|
| Setup | zero dependencies | `pip install sqlalchemy` |
| Style | raw SQL strings | Python classes/objects |
| Portability | SQLite only | works with SQLite, PostgreSQL, MySQL, etc. with little code change |
| Best for | small scripts, simple embedded storage | applications that grow, need multiple DB backends, or many relationships |

## Exercise

Using plain `sqlite3`, create a `tasks` table (`id`, `title`, `done`) and write
functions `add_task`, `complete_task`, `list_tasks` using parameterized
queries. Then rebuild the same thing with SQLAlchemy: a `Task` model class and
equivalent CRUD functions using a `Session`. Compare how much code each
approach needs, and note in a comment which you'd pick for a project expected
to grow to 20+ tables.
