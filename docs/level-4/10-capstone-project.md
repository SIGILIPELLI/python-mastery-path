# 10 · Capstone Project

The final project ties together everything from all four levels: a
production-shaped FastAPI service with a real database, authentication,
structured errors, a full `pytest` suite, a Dockerfile, and a CI pipeline.
It's a "Habit Tracker" API — users register, log in, create habits, and
record daily check-ins.

## What you'll build

- JWT-based authentication (register + login)
- SQLite database via SQLAlchemy, with a `User` -> `Habit` -> `CheckIn`
  relationship
- Full CRUD for habits, scoped to the authenticated user
- Custom exception classes mapped to clean HTTP error responses
- A `pytest` suite covering auth, CRUD, and access-control edge cases
- A `Dockerfile` and a GitHub Actions CI workflow

## Project layout

```text
habit_tracker/
    app/
        __init__.py
        database.py
        models.py
        schemas.py
        security.py
        crud.py
        errors.py
        main.py
    tests/
        conftest.py
        test_auth.py
        test_habits.py
    requirements.txt
    requirements-dev.txt
    Dockerfile
    .github/
        workflows/
            ci.yml
```

## requirements.txt

```text
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
"python-jose[cryptography]"==3.3.0
"passlib[bcrypt]"==1.7.4
pydantic-settings==2.3.0
```

## requirements-dev.txt

```text
-r requirements.txt
pytest==8.2.0
httpx==0.27.0
pytest-cov==5.0.0
```

## app/database.py

```python
# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./habits.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## app/models.py

```python
# app/models.py
from datetime import date
from sqlalchemy import String, Integer, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    habits: Mapped[List["Habit"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="habits")
    check_ins: Mapped[List["CheckIn"]] = relationship(back_populates="habit", cascade="all, delete-orphan")


class CheckIn(Base):
    __tablename__ = "check_ins"
    __table_args__ = (UniqueConstraint("habit_id", "day", name="one_checkin_per_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"))
    day: Mapped[date] = mapped_column(Date)

    habit: Mapped["Habit"] = relationship(back_populates="check_ins")
```

The `UniqueConstraint` on `(habit_id, day)` enforces at the database level
that a habit can only be checked in once per day — a good example of pushing
an invariant down to the data layer instead of trusting application code alone.

## app/errors.py

```python
# app/errors.py

class HabitTrackerError(Exception):
    """Base class for all domain errors in this app."""


class UsernameTakenError(HabitTrackerError):
    def __init__(self, username):
        super().__init__(f"username '{username}' is already taken")


class InvalidCredentialsError(HabitTrackerError):
    def __init__(self):
        super().__init__("invalid username or password")


class HabitNotFoundError(HabitTrackerError):
    def __init__(self, habit_id):
        super().__init__(f"no habit with id {habit_id}")


class AlreadyCheckedInError(HabitTrackerError):
    def __init__(self, day):
        super().__init__(f"already checked in for {day}")
```

## app/security.py

```python
# app/security.py
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_error
    return user
```

## app/schemas.py

```python
# app/schemas.py
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=100)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CheckInCreate(BaseModel):
    day: date


class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    day: date


class HabitWithCheckIns(HabitOut):
    check_ins: list[CheckInOut] = []
```

## app/crud.py

```python
# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models, schemas, security, errors


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise errors.UsernameTakenError(user.username)

    db_user = models.User(username=user.username, hashed_password=security.hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> models.User:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise errors.InvalidCredentialsError()
    return user


def create_habit(db: Session, owner: models.User, habit: schemas.HabitCreate) -> models.Habit:
    db_habit = models.Habit(name=habit.name, owner_id=owner.id)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


def list_habits(db: Session, owner: models.User) -> list[models.Habit]:
    return db.query(models.Habit).filter(models.Habit.owner_id == owner.id).all()


def get_owned_habit(db: Session, owner: models.User, habit_id: int) -> models.Habit:
    habit = (
        db.query(models.Habit)
        .filter(models.Habit.id == habit_id, models.Habit.owner_id == owner.id)
        .first()
    )
    if habit is None:
        raise errors.HabitNotFoundError(habit_id)
    return habit


def delete_habit(db: Session, owner: models.User, habit_id: int) -> None:
    habit = get_owned_habit(db, owner, habit_id)
    db.delete(habit)
    db.commit()


def add_check_in(db: Session, owner: models.User, habit_id: int, check_in: schemas.CheckInCreate) -> models.CheckIn:
    habit = get_owned_habit(db, owner, habit_id)
    db_check_in = models.CheckIn(habit_id=habit.id, day=check_in.day)
    db.add(db_check_in)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise errors.AlreadyCheckedInError(check_in.day)
    db.refresh(db_check_in)
    return db_check_in
```

Every habit-scoped query filters by `owner_id == owner.id` — this is the
access-control core of the app: a user can never read, modify, or check in on
another user's habits, enforced at the query level rather than trusted to be
checked ad hoc in each route.

## app/main.py

```python
# app/main.py
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import crud, schemas, security, errors
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Habit Tracker API")


@app.exception_handler(errors.HabitTrackerError)
async def domain_error_handler(request: Request, exc: errors.HabitTrackerError):
    status_map = {
        errors.UsernameTakenError: 409,
        errors.InvalidCredentialsError: 401,
        errors.HabitNotFoundError: 404,
        errors.AlreadyCheckedInError: 409,
    }
    status_code = status_map.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"error": str(exc)})


@app.post("/auth/register", response_model=schemas.HabitOut, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, user)
    return {"id": db_user.id, "name": db_user.username}


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    token = security.create_access_token(user.username)
    return schemas.Token(access_token=token)


@app.post("/habits", response_model=schemas.HabitOut, status_code=201)
def create_habit(
    habit: schemas.HabitCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    return crud.create_habit(db, current_user, habit)


@app.get("/habits", response_model=list[schemas.HabitOut])
def list_habits(db: Session = Depends(get_db), current_user=Depends(security.get_current_user)):
    return crud.list_habits(db, current_user)


@app.get("/habits/{habit_id}", response_model=schemas.HabitWithCheckIns)
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    return crud.get_owned_habit(db, current_user, habit_id)


@app.delete("/habits/{habit_id}", status_code=204)
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    crud.delete_habit(db, current_user, habit_id)


@app.post("/habits/{habit_id}/check-ins", response_model=schemas.CheckInOut, status_code=201)
def check_in(
    habit_id: int,
    check_in: schemas.CheckInCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    return crud.add_check_in(db, current_user, habit_id, check_in)
```

The single `domain_error_handler` translates every custom exception into the
right HTTP status code in one place, keeping routes focused on orchestration
rather than error-formatting boilerplate.

## tests/conftest.py

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers a user and returns Authorization headers for it."""
    client.post("/auth/register", json={"username": "ada", "password": "secretpass123"})
    response = client.post("/auth/login", data={"username": "ada", "password": "secretpass123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## tests/test_auth.py

```python
# tests/test_auth.py

def test_register_creates_user(client):
    response = client.post("/auth/register", json={"username": "grace", "password": "hopperpass1"})
    assert response.status_code == 201


def test_register_rejects_duplicate_username(client):
    client.post("/auth/register", json={"username": "grace", "password": "hopperpass1"})
    response = client.post("/auth/register", json={"username": "grace", "password": "anotherpass"})
    assert response.status_code == 409


def test_login_success(client):
    client.post("/auth/register", json={"username": "ada", "password": "secretpass123"})
    response = client.post("/auth/login", data={"username": "ada", "password": "secretpass123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "ada", "password": "secretpass123"})
    response = client.post("/auth/login", data={"username": "ada", "password": "wrongpass"})
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/habits")
    assert response.status_code == 401
```

## tests/test_habits.py

```python
# tests/test_habits.py

def test_create_and_list_habits(client, auth_headers):
    client.post("/habits", json={"name": "Read 20 minutes"}, headers=auth_headers)
    response = client.get("/habits", headers=auth_headers)

    assert response.status_code == 200
    names = [h["name"] for h in response.json()]
    assert "Read 20 minutes" in names


def test_check_in_and_prevent_duplicate(client, auth_headers):
    habit = client.post("/habits", json={"name": "Exercise"}, headers=auth_headers).json()

    first = client.post(
        f"/habits/{habit['id']}/check-ins", json={"day": "2026-07-18"}, headers=auth_headers
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/habits/{habit['id']}/check-ins", json={"day": "2026-07-18"}, headers=auth_headers
    )
    assert duplicate.status_code == 409


def test_get_habit_includes_check_ins(client, auth_headers):
    habit = client.post("/habits", json={"name": "Meditate"}, headers=auth_headers).json()
    client.post(f"/habits/{habit['id']}/check-ins", json={"day": "2026-07-18"}, headers=auth_headers)

    response = client.get(f"/habits/{habit['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["check_ins"]) == 1


def test_users_cannot_access_each_others_habits(client):
    client.post("/auth/register", json={"username": "ada", "password": "secretpass123"})
    ada_token = client.post("/auth/login", data={"username": "ada", "password": "secretpass123"}).json()["access_token"]
    ada_headers = {"Authorization": f"Bearer {ada_token}"}

    client.post("/auth/register", json={"username": "grace", "password": "hopperpass1"})
    grace_token = client.post("/auth/login", data={"username": "grace", "password": "hopperpass1"}).json()["access_token"]
    grace_headers = {"Authorization": f"Bearer {grace_token}"}

    habit = client.post("/habits", json={"name": "Ada's secret habit"}, headers=ada_headers).json()

    response = client.get(f"/habits/{habit['id']}", headers=grace_headers)
    assert response.status_code == 404   # not 403 — we don't reveal that the resource exists at all
```

The last test is the most important one in the whole suite: it proves the
access-control model actually works end-to-end, not just that the CRUD
functions exist.

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## .github/workflows/ci.yml

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app --cov-report=term-missing

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t habit-tracker:${{ github.sha }} .
```

## Running everything locally

```bash
pip install -r requirements-dev.txt
pytest --cov=app -v

uvicorn app.main:app --reload
# POST /auth/register {"username": "ada", "password": "secretpass123"}
# POST /auth/login     (form data: username, password) -> access_token
# POST /habits         (Authorization: Bearer <token>) {"name": "Read 20 minutes"}
# POST /habits/1/check-ins  {"day": "2026-07-18"}
```

## What this project demonstrates, level by level

| Level | Concept | Where |
|-------|---------|-------|
| 1 | Functions, control flow, file/data structures | throughout |
| 2 | OOP (models), custom exceptions, testing basics | `models.py`, `errors.py`, `tests/` |
| 3 | SQLAlchemy, building APIs with FastAPI, consuming/returning JSON | `database.py`, `main.py` |
| 4 | Auth & middleware-style error handling, testing at scale, Docker/CI, security practices | `security.py`, `conftest.py`, `Dockerfile`, `ci.yml` |

## Stretch goals

- Add a `GET /habits/{id}/streak` endpoint computing the current consecutive
  check-in streak.
- Add rate limiting to `/auth/login` to slow down credential-stuffing attempts
  (tying back to [Production-Grade APIs](04-production-apis.md)).
- Swap SQLite for Postgres via `docker-compose`, as in
  [Deployment & DevOps](08-deployment-devops.md).

Completing this project means you've finished **Python Mastery Path** —
entry level through master level, with real, working code at every step.
