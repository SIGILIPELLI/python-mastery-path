# 09 · Security Best Practices

Writing correct, well-tested code isn't enough if it's also exploitable. This
module covers secrets management, input validation, and the vulnerability
classes that show up most often in real Python applications.

## Secrets management

Never hard-code credentials, API keys, or tokens into source code — they end
up in version control history permanently, even if removed later.

```python
# WRONG — never do this:
API_KEY = "sk_live_abc123realkeyhere"

# RIGHT — read from the environment:
import os

api_key = os.environ.get("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY environment variable must be set")
```

For production systems, a dedicated secrets manager (AWS Secrets Manager,
HashiCorp Vault, environment injection from your deployment platform) is
preferable to plain `.env` files, since it supports rotation, access
auditing, and avoids secrets ever touching disk in plain text.

```bash
# scanning a repo for accidentally committed secrets before they go further
pip install detect-secrets
detect-secrets scan
```

## Input validation

Treat all external input — form data, query parameters, JSON bodies, file
uploads — as untrusted until validated.

```python
from pydantic import BaseModel, Field, field_validator

class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: str
    age: int = Field(ge=13, le=120)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value):
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("invalid email format")
        return value.lower()
```

Pydantic (already used throughout Level 3/4's FastAPI modules) rejects
malformed input automatically, before it ever reaches your business logic.

## SQL injection

Covered in [Databases](../level-3/06-databases.md), but worth repeating as a
security rule: never build SQL by string concatenation or f-strings with
untrusted values.

```python
# VULNERABLE — an attacker-controlled `username` could inject SQL:
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)
# if username = "' OR '1'='1", this returns every row in the table

# SAFE — parameterized queries let the database driver handle escaping:
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

ORMs like SQLAlchemy parameterize queries for you automatically as long as
you build filters through the ORM's own API rather than raw string
interpolation.

## Cross-site scripting (XSS) basics

If your application renders user-supplied text into HTML, an attacker can
inject `<script>` tags that run in other users' browsers unless the output is
escaped.

```python
# templating engines like Jinja2 (used by Flask/FastAPI) auto-escape by default:
from jinja2 import Template

template = Template("<p>Hello, {{ name }}!</p>")
print(template.render(name="<script>alert('xss')</script>"))
# <p>Hello, &lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;!</p>
```

The danger appears when auto-escaping is explicitly disabled (`{{ name | safe }}`
in Jinja2, or manually concatenating raw strings into HTML) — avoid that
unless you fully control and trust the content.

## Command injection

Never build shell commands from untrusted input.

```python
import subprocess

# VULNERABLE:
filename = "report.txt; rm -rf /"
subprocess.run(f"cat {filename}", shell=True)   # NEVER pass untrusted input with shell=True

# SAFE — pass arguments as a list, no shell involved:
subprocess.run(["cat", filename])   # the ";" is just a literal character in the filename now
```

`shell=True` combined with string interpolation is one of the most dangerous,
common patterns in real codebases — avoid `shell=True` entirely unless you
fully control every part of the command string.

## Deserialization risks

`pickle` can execute arbitrary code during deserialization — never
`pickle.load` data from an untrusted source.

```python
import pickle

# NEVER unpickle data from users, network requests, or any untrusted source:
# data = pickle.loads(untrusted_bytes)   # can execute arbitrary code

# prefer JSON for untrusted data — it can only represent plain data, never code:
import json
data = json.loads(untrusted_text)
```

## Password storage

Never store plain-text or reversibly-encrypted passwords. Use a slow, salted
hashing algorithm designed for passwords.

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed = pwd_context.hash("user-supplied-password")
print(pwd_context.verify("user-supplied-password", hashed))   # True
print(pwd_context.verify("wrong-guess", hashed))                # False
```

`bcrypt` (and similar algorithms like `argon2`) are deliberately slow to
compute, which makes brute-forcing stolen password hashes far more expensive
for an attacker than a fast general-purpose hash like plain SHA-256.

## Dependency vulnerabilities

Third-party packages can carry known vulnerabilities — scan for them
regularly, not just once.

```bash
pip install pip-audit
pip-audit
```

```text
Found 1 known vulnerability in 1 package
Name     Version ID             Fix Versions
-------- ------- -------------- -------------
requests 2.25.0  PYSEC-2023-74  2.31.0
```

## Least privilege

Grant every component (database users, API tokens, container processes) only
the permissions it actually needs.

```sql
-- a reporting service should never have write access:
CREATE USER reporting_user WITH PASSWORD '...';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reporting_user;
-- deliberately NOT granting INSERT/UPDATE/DELETE
```

## Cheat sheet — common vulnerability classes

| Vulnerability | Cause | Prevention |
|----------------|-------|-------------|
| SQL injection | string-built queries with untrusted input | parameterized queries / ORM |
| XSS | unescaped user input rendered as HTML | auto-escaping templates, avoid `\| safe` |
| Command injection | `shell=True` with untrusted input | pass argument lists, avoid `shell=True` |
| Insecure deserialization | `pickle.load` on untrusted data | use JSON for untrusted data |
| Weak password storage | fast/reversible hashing, or plain text | bcrypt/argon2 via `passlib` |
| Hard-coded secrets | credentials committed to source | environment variables / secrets manager |
| Known-vulnerable dependencies | outdated packages | `pip-audit` in CI |

## How It Actually Works

SQL injection, XSS, and command injection are structurally the *same* underlying
bug, just in three different interpreters: each is a case of untrusted data being
concatenated into a string that a downstream parser will then interpret as *syntax*
rather than as inert *data*. A SQL engine's parser can't tell the difference between
`'` characters you meant as literal text and `'` characters that close a string and
start new SQL grammar; a browser's HTML parser can't tell `<script>` you meant as
plain text from `<script>` you meant as a tag; a shell's parser can't tell a `;` you
meant as a literal filename character from a `;` meant to start a second command.
Parameterized queries, HTML auto-escaping, and `subprocess.run([...])` (a list, not
a string) all solve this the same way: they keep the untrusted data on a separate
channel from the syntax being parsed, so the parser is structurally incapable of
reinterpreting it, rather than relying on you correctly guessing every dangerous
character to filter out — `shell=True` specifically routes your command through
`/bin/sh -c "..."`, handing the *interpolated string itself* to a real shell parser
that respects `;`, `|`, `&&`, backticks, and more, which is exactly the syntax
channel a list-of-arguments call bypasses entirely by invoking the target program
directly via `execve` with no shell in between.

`pickle.load` executing arbitrary code on untrusted input isn't a bug in `pickle` —
it's an inherent consequence of what pickle's format is designed to do: a pickle
stream isn't just serialized data, it's effectively a small stack-based bytecode
program (its own opcode set, distinct from CPython's) that reconstructs arbitrary
Python objects, including instances of arbitrary classes — and one of its opcodes
(`REDUCE`, or `GLOBAL` followed by a call) is explicitly designed to call a named
callable with given arguments during deserialization, because that's how pickle
reconstructs objects whose type defines a custom `__reduce__`. There's no way to
sandbox this partially: unpickling is *supposed* to be able to invoke code, which is
precisely what makes it unsafe for anything you didn't generate yourself. `json.loads`
has no equivalent capability by design — its grammar (Module 5's recursive-descent
parser) can only ever build `dict`/`list`/`str`/`int`/`float`/`bool`/`None`, with
no opcode anywhere in the format for "now call this function."

`pwd_context.verify(...)` from Module 4 is the same mechanism repeated here for
emphasis: bcrypt's embedded salt and deliberately expensive cost factor make brute-
forcing a *stolen hash* computationally expensive per guess even with full offline
access to it, which is the actual threat model password hashing defends against — a
fast hash like SHA-256 is designed for the opposite property (verifying huge
volumes of data quickly), which is exactly why it's the wrong tool here despite
technically being "a hash."

`GRANT SELECT ... (deliberately NOT granting INSERT/UPDATE/DELETE)` works because a
database's permission system is checked by the query planner *before* a statement
is allowed to execute — the same enforcement point that would reject a malformed
query rejects an `UPDATE` from a connection authenticated as `reporting_user`
regardless of what the application code sitting on top of that connection tries to
do. This is the concrete value of least privilege: even if every other layer
(application logic, SQL injection defenses) somehow failed simultaneously, a
compromised reporting service literally cannot issue a write the database engine
itself will execute, because the permission check happens at a lower layer than any
application bug could reach.

## Exercise

Audit the Level 3/4 Book Catalog API for the issues in this module: confirm
all database access goes through the SQLAlchemy ORM (no raw string-built
SQL), add `pydantic` field validation limiting `title`/`author` length and
rejecting obviously malicious characters, wire `pip-audit` into the CI
workflow from the previous module as an extra job, and write a short
comment explaining why the JWT `SECRET_KEY` from
[Production-Grade APIs](04-production-apis.md) must come from an environment
variable in any real deployment rather than the hard-coded example value.
