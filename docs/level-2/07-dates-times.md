# 07 · Dates & Times

Nearly every real application deals with dates and times somewhere: timestamps
in logs, expiration dates, scheduling. Python's `datetime` module is the
standard tool for representing, comparing, and formatting them.

## `date`, `time`, and `datetime`

```python
from datetime import date, time, datetime

d = date(2026, 7, 18)
t = time(14, 30, 0)
dt = datetime(2026, 7, 18, 14, 30, 0)

print(d)     # 2026-07-18
print(t)     # 14:30:00
print(dt)    # 2026-07-18 14:30:00

now = datetime.now()          # current local date & time
today = date.today()          # current local date
print(now.year, now.month, now.day, now.hour, now.minute)
```

## `timedelta` — durations and date arithmetic

```python
from datetime import datetime, timedelta

start = datetime(2026, 1, 1)
one_week_later = start + timedelta(weeks=1)
ninety_days_later = start + timedelta(days=90)

print(one_week_later)      # 2026-01-08 00:00:00
print(ninety_days_later)   # 2026-04-01 00:00:00

deadline = datetime(2026, 12, 31)
remaining = deadline - datetime.now()
print(remaining.days, "days left")
```

`timedelta` objects support arithmetic (`+`, `-`) and comparisons directly with
`datetime`/`date` objects.

## Comparing dates and times

```python
from datetime import date

release = date(2026, 7, 1)
today = date.today()

if today >= release:
    print("released")
else:
    print(f"{ (release - today).days } days until release")
```

## Formatting dates: `strftime`

`strftime` ("string format time") converts a `datetime` into a string using
format codes.

```python
from datetime import datetime

dt = datetime(2026, 7, 18, 9, 5, 0)

print(dt.strftime("%Y-%m-%d"))            # 2026-07-18
print(dt.strftime("%B %d, %Y"))           # July 18, 2026
print(dt.strftime("%A, %I:%M %p"))        # Saturday, 09:05 AM
print(dt.isoformat())                      # 2026-07-18T09:05:00 — standard ISO 8601
```

| Code | Meaning | Example |
|------|---------|---------|
| `%Y` | 4-digit year | 2026 |
| `%m` | zero-padded month | 07 |
| `%d` | zero-padded day | 18 |
| `%H` / `%I` | hour (24h / 12h) | 09 |
| `%M` | minute | 05 |
| `%B` | full month name | July |
| `%A` | full weekday name | Saturday |
| `%p` | AM/PM | AM |

## Parsing dates: `strptime`

`strptime` ("string parse time") is the reverse: it turns a string into a
`datetime`, given the format it's written in.

```python
from datetime import datetime

parsed = datetime.strptime("2026-07-18 09:05", "%Y-%m-%d %H:%M")
print(parsed.year, parsed.hour)   # 2026 9

# ISO 8601 strings can be parsed directly, without a format string:
parsed_iso = datetime.fromisoformat("2026-07-18T09:05:00")
```

If the format string doesn't match the actual text, `strptime` raises
`ValueError` — worth catching when parsing user- or file-supplied dates.

```python
def parse_date_safe(text, fmt="%Y-%m-%d"):
    try:
        return datetime.strptime(text, fmt)
    except ValueError:
        return None
```

## Time zones

Naive `datetime` objects (the ones we've made so far) carry no timezone
information. Python 3.9+ ships `zoneinfo` in the standard library for real IANA
timezone support.

```python
from datetime import datetime
from zoneinfo import ZoneInfo

utc_now = datetime.now(ZoneInfo("UTC"))
ny_now = utc_now.astimezone(ZoneInfo("America/New_York"))
tokyo_now = utc_now.astimezone(ZoneInfo("Asia/Tokyo"))

print(utc_now)
print(ny_now)
print(tokyo_now)

# attaching a timezone to a naive datetime (assumes it already represents that zone):
meeting = datetime(2026, 7, 18, 15, 0, tzinfo=ZoneInfo("Europe/London"))
meeting_in_sf = meeting.astimezone(ZoneInfo("America/Los_Angeles"))
print(meeting_in_sf)
```

Comparing or subtracting a naive `datetime` and an aware one raises
`TypeError` — always keep track of which kind you're working with, and prefer
timezone-aware datetimes for anything involving more than one location.

## Cheat sheet

| Task | Tool |
|------|------|
| Current local time | `datetime.now()` |
| Current UTC time | `datetime.now(ZoneInfo("UTC"))` |
| Add/subtract time | `timedelta(days=..., hours=...)` |
| `datetime` -> string | `.strftime(fmt)` or `.isoformat()` |
| string -> `datetime` | `datetime.strptime(text, fmt)` or `.fromisoformat()` |
| Convert timezone | `.astimezone(ZoneInfo("..."))` |

## Exercise

Write a function `days_until_birthday(birth_month, birth_day)` that returns
how many days remain until the next occurrence of that month/day (handling the
case where it has already passed this year, so it should count toward next
year instead). Then write `format_countdown(target: datetime)` that returns a
human string like `"3 days, 4 hours remaining"` using a `timedelta`.
