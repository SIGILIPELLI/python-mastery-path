# 06 · Regular Expressions

Regular expressions describe patterns in text. Python's `re` module lets you
search, extract, validate, and replace text based on those patterns instead of
writing manual character-by-character parsing.

## Basic pattern syntax

| Pattern | Matches |
|---------|---------|
| `.` | any character except newline |
| `\d` | a digit (`0-9`) |
| `\w` | a "word" character (letters, digits, underscore) |
| `\s` | whitespace |
| `*` | 0 or more of the previous token |
| `+` | 1 or more of the previous token |
| `?` | 0 or 1 of the previous token (also: makes `*`/`+` non-greedy) |
| `{n,m}` | between n and m repetitions |
| `^` / `$` | start / end of string (or line, with `re.MULTILINE`) |
| `[abc]` | any one of `a`, `b`, `c` |
| `(...)` | a capturing group |
| `\|` | alternation ("or") |

## `re.search` vs `re.match` vs `re.fullmatch`

```python
import re

text = "order #4821 shipped"

print(re.match(r"\d+", text))       # None — match() only anchors at the START of the string
print(re.search(r"\d+", text))      # <Match object; span=(7, 11), match='4821'> — searches anywhere
print(re.fullmatch(r"order.*", text))  # matches only if the WHOLE string fits the pattern
```

`re.match` is a common source of confusion: it silently anchors to position 0,
so a pattern that would obviously match "somewhere" in the string returns
`None` if that text isn't right at the start. `re.search` is usually what you
want.

## `findall` and `finditer`

```python
log = "user=42 action=login user=7 action=logout"

ids = re.findall(r"user=(\d+)", log)
print(ids)   # ['42', '7'] — findall returns just the captured groups

for match in re.finditer(r"user=(\d+)", log):
    print(match.group(0), "->", match.group(1), "at", match.span())
# user=42 -> 42 at (0, 8)
# user=7 -> 7 at (24, 31)
```

`finditer` gives you full `Match` objects (position, groups) instead of just
the captured strings.

## Groups — capturing and naming

```python
pattern = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
match = re.search(pattern, "Event date: 2026-07-18")

print(match.group())          # 2026-07-18 (the whole match)
print(match.group("year"))    # 2026
print(match.groupdict())      # {'year': '2026', 'month': '07', 'day': '18'}
```

Named groups (`(?P<name>...)`) make code that uses the match far more
readable than relying on numeric group positions.

## `sub` — search and replace

```python
messy = "Contact:  john@example.com , jane@example.com"

# collapse multiple spaces into one
cleaned = re.sub(r"\s+", " ", messy)
print(cleaned)   # Contact: john@example.com , jane@example.com

# redact emails
redacted = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email hidden]", messy)
print(redacted)  # Contact:  [email hidden] , [email hidden]
```

`sub` also accepts a function instead of a replacement string, called once per
match:

```python
def censor(match):
    return "*" * len(match.group())

print(re.sub(r"\d{4,}", censor, "card 483920 exp 1225"))
# card ****** exp 1225
```

## Compiling patterns for reuse

If you use the same pattern repeatedly (e.g. inside a loop), compile it once.

```python
phone_pattern = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

texts = ["call 555-123-4567", "or (555) 987 6543", "no number here"]
for t in texts:
    match = phone_pattern.search(t)
    if match:
        print(match.group())
# 555-123-4567
# (555) 987 6543
```

## Greedy vs. non-greedy

```python
html = "<b>bold</b> and <i>italic</i>"

greedy = re.findall(r"<.*>", html)           # greedy: grabs as much as possible
non_greedy = re.findall(r"<.*?>", html)       # non-greedy: stops at the first match

print(greedy)      # ['<b>bold</b> and <i>italic</i>']
print(non_greedy)  # ['<b>', '</b>', '<i>', '</i>']
```

## Common flags

```python
re.search(r"python", "I love Python", re.IGNORECASE)   # case-insensitive
re.findall(r"^\d+", "1 apple\n2 pears", re.MULTILINE)   # ^ matches start of EACH line
```

## Exercise

Write a function `extract_hashtags(text)` that returns a list of unique
hashtags (without the `#`) found in a piece of text using `re.findall`, and a
function `mask_credit_cards(text)` that replaces any 16-digit number
(optionally separated by spaces or dashes into groups of 4) with
`"**** **** **** " + last 4 digits`, using a named group and `re.sub`.
