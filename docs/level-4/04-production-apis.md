# 04 · Production-Grade APIs

Level 3 built working FastAPI CRUD services. Taking an API to production adds
concerns that don't show up in a demo: authentication, cross-cutting
middleware, versioning strategy, and protecting the service from abuse via
rate limiting.

## Authentication with OAuth2 password flow + JWT

```bash
pip install "python-jose[cryptography]" "passlib[bcrypt]"
```

```python
# auth.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "change-me-in-production"   # in real code: load from an env var / secrets manager
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
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
        return username
    except JWTError:
        raise credentials_error
```

Passwords are never stored in plain text — only `hash_password`'s bcrypt
output is persisted, and `verify_password` checks a login attempt against
that hash.

## Wiring authentication into routes

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)

app = FastAPI()

# in real code this is a database table, not an in-memory dict
fake_users_db = {"ada": {"username": "ada", "hashed_password": hash_password("secret123")}}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect username or password")
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def read_current_user(username: str = Depends(get_current_user)):
    return {"username": username}
```

## Middleware — cross-cutting request/response logic

Middleware runs for every request, useful for logging, timing, or adding
headers without repeating code in every route.

```python
import time
import uuid
from fastapi import FastAPI, Request

app = FastAPI()


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)   # runs the actual route handler

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{duration_ms:.2f}"
    print(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response
```

## CORS middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myfrontend.example.com"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

Never use `allow_origins=["*"]` together with `allow_credentials=True` in
production — that combination effectively disables the browser's same-origin
protections for authenticated requests.

## API versioning

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()

v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")


@v1_router.get("/books/{book_id}")
def get_book_v1(book_id: int):
    return {"id": book_id, "title": "Legacy shape"}


@v2_router.get("/books/{book_id}")
def get_book_v2(book_id: int):
    return {"id": book_id, "title": "New shape", "metadata": {"schema_version": 2}}


app.include_router(v1_router)
app.include_router(v2_router)
```

Prefix-based versioning (`/api/v1`, `/api/v2`) is the simplest and most
common approach — it lets you retire an old version on its own schedule
without breaking clients still pinned to it.

## Rate limiting

```bash
pip install slowapi
```

```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/search")
@limiter.limit("5/minute")
def search(request: "Request"):
    return {"results": []}
```

`get_remote_address` keys the limit per client IP; a well-behaved client
exceeding 5 requests/minute gets a `429 Too Many Requests` response instead of
overwhelming the server.

## Structured error responses

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "path": str(request.url.path)},
    )
```

A global exception handler like this ensures every error the API returns has
a consistent JSON shape, rather than each route formatting errors differently.

## Cheat sheet

| Concern | Tool |
|---------|------|
| Login & tokens | OAuth2 password flow + JWT (`python-jose`) |
| Password storage | `passlib` with bcrypt, never plain text |
| Cross-cutting logic | `@app.middleware("http")` |
| Cross-origin requests | `CORSMiddleware` (explicit origins, not `*` with credentials) |
| API evolution | prefix-based routers (`/api/v1`, `/api/v2`) |
| Abuse protection | `slowapi` rate limiting |
| Consistent error shape | `@app.exception_handler(...)` |

## How It Actually Works

`pwd_context.hash(password)` doesn't just run one hash function — bcrypt combines a
randomly generated **salt** with the password and runs the result through the
Blowfish-derived cipher a configurable number of rounds (a "cost factor," commonly
2^12 or higher), producing an output string that embeds the salt, the cost factor,
and the hash together. This is deliberately, tunably slow: a fast general-purpose
hash like SHA-256 can be brute-forced at billions of guesses per second on commodity
hardware, while bcrypt's cost factor can be dialed up over time to keep pace with
faster hardware, and the embedded random salt means two users with the identical
password get completely different stored hashes — defeating precomputed
("rainbow table") attacks. `verify_password` re-derives the hash using the *same*
embedded salt and cost factor pulled out of the stored string, then compares the
result — it never "decrypts" anything, because there's nothing reversible here at
all.

A JWT is not encrypted (with `HS256` specifically) — `jwt.encode` builds a header and
a payload dict (your data plus `exp`), base64url-encodes each separately, and
computes an **HMAC-SHA256 signature** over the concatenated header and payload using
`SECRET_KEY`, appending that as a third dot-separated segment. Anyone can decode the
header and payload from a JWT with no key at all (they're just base64, not
encryption) — the entire security property lives in the third segment: only someone
holding `SECRET_KEY` can produce a signature that will verify, so `jwt.decode`
recomputes the HMAC from the received header/payload and rejects the token (raising
`JWTError`) if it doesn't match, which is exactly why a stolen or forged token
without the real secret is worthless even though its contents are fully readable.

`@app.middleware("http")` works by wrapping every route handler in an onion of
nested async calls: FastAPI (built on Starlette) chains each registered middleware
function so that `call_next(request)` inside your `add_request_id_and_timing`
function is itself a call into the next layer of that chain — either another
middleware or, at the innermost layer, the matched route handler. Because your code
runs both *before* `await call_next(request)` (timing starts, request ID generated)
and *after* it returns (headers added to the real response object), the same
function naturally wraps every request regardless of which route ultimately handles
it — there's no need to duplicate that logic in each route function.

Prefix-based versioning (`APIRouter(prefix="/api/v1")`) works through simple path
matching at request-dispatch time: FastAPI/Starlette's router holds an ordered list
of (path pattern, handler) pairs, and `include_router` just merges each router's
routes into that list with the prefix prepended to every path pattern — a request
for `/api/v1/books/3` and one for `/api/v2/books/3` are matched against entirely
separate compiled path patterns pointing at entirely separate handler functions, so
"v1" and "v2" coexisting is simply two independent entries in the same routing
table, not any kind of runtime branching inside one shared handler.

## Exercise

Take the Book Catalog API from Level 3's capstone project and add: a
`/token` login endpoint and JWT-protected `POST`/`PATCH`/`DELETE` routes
(reads stay public), a logging middleware that records method, path, status
code, and duration for every request, and a `20/minute` rate limit on the
public `GET /books` endpoint. Write a test that confirms an unauthenticated
`POST /books` returns `401`.
