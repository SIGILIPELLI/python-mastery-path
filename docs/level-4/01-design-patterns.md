# 01 · Design Patterns in Python

Design patterns are named, reusable solutions to common design problems. This
module covers four of the most useful ones day-to-day, implemented in a way
that leans on Python's own features (first-class functions, modules as
singletons) rather than translating them literally from a language like Java.

## Factory pattern

A factory centralizes object creation logic, so callers don't need to know
which concrete class to instantiate.

```python
from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None: ...


class EmailNotifier(Notifier):
    def send(self, message: str) -> None:
        print(f"Emailing: {message}")


class SMSNotifier(Notifier):
    def send(self, message: str) -> None:
        print(f"Texting: {message}")


def notifier_factory(kind: str) -> Notifier:
    notifiers = {"email": EmailNotifier, "sms": SMSNotifier}
    try:
        return notifiers[kind]()
    except KeyError:
        raise ValueError(f"unknown notifier kind: {kind!r}")


notifier = notifier_factory("email")
notifier.send("Your order shipped!")
```

Adding a new notifier type means adding one entry to the dict, not scattering
`if/elif` chains across the codebase.

## Strategy pattern

Strategy lets you swap an algorithm at runtime by passing in different
behavior — in Python this is often just a function, no class hierarchy
required.

```python
def total_price(items, discount_strategy):
    subtotal = sum(item["price"] for item in items)
    return discount_strategy(subtotal)


def no_discount(subtotal):
    return subtotal

def ten_percent_off(subtotal):
    return subtotal * 0.9

def bulk_discount(subtotal):
    return subtotal * 0.8 if subtotal > 100 else subtotal


items = [{"price": 40}, {"price": 70}]
print(total_price(items, no_discount))       # 110
print(total_price(items, ten_percent_off))    # 99.0
print(total_price(items, bulk_discount))      # 88.0
```

Each "strategy" is just a plain function with a matching signature — no
`Strategy` base class needed, thanks to Python's first-class functions.

## Observer pattern

Observer lets one object ("subject") notify a list of interested listeners
whenever something happens, without the subject knowing anything about them.

```python
class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        self._subscribers.setdefault(event_name, []).append(callback)

    def publish(self, event_name, **data):
        for callback in self._subscribers.get(event_name, []):
            callback(**data)


bus = EventBus()

def send_confirmation_email(order_id, total):
    print(f"Emailing confirmation for order {order_id} (${total})")

def update_inventory(order_id, total):
    print(f"Updating inventory for order {order_id}")

bus.subscribe("order_placed", send_confirmation_email)
bus.subscribe("order_placed", update_inventory)

bus.publish("order_placed", order_id=42, total=79.99)
# Emailing confirmation for order 42 ($79.99)
# Updating inventory for order 42
```

This is the same core idea behind GUI event handlers, webhooks, and pub/sub
message queues — a subject publishes events, and any number of decoupled
listeners react.

## Singleton pattern

Singleton ensures a class has exactly one instance. In Python, a module is
already a singleton (it's only ever imported once and cached in
`sys.modules`), which is usually the simplest and most Pythonic way to share
one piece of global state — no class needed at all.

```python
# config.py — a module used as a singleton
_settings = {"debug": False, "api_url": "https://api.example.com"}

def get(key):
    return _settings[key]

def set(key, value):
    _settings[key] = value
```

```python
import config
config.set("debug", True)

# anywhere else that imports config, it's the SAME dict — modules are cached
import config as config_again
print(config_again.get("debug"))   # True
```

If you do need a class-based singleton (e.g. because it needs `__init__`
arguments the first time it's created), override `__new__`:

```python
class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logs = []
        return cls._instance

    def log(self, message):
        self.logs.append(message)


a = Logger()
b = Logger()
a.log("first entry")
print(a is b)          # True — same object
print(b.logs)           # ['first entry'] — shared state
```

## Choosing a pattern

| Pattern | Problem it solves | Pythonic shortcut |
|---------|--------------------|--------------------|
| Factory | centralize "which class do I create?" logic | a dict of constructors |
| Strategy | swap an algorithm at runtime | pass a plain function |
| Observer | decouple "something happened" from "who reacts" | a dict of `event -> [callbacks]` |
| Singleton | exactly one shared instance | a module (not a class) |

## Exercise

Build a small "report exporter" using the strategy pattern: a function
`export_report(data, format_strategy)` that accepts strategies
`as_csv_text`, `as_json_text`, and `as_markdown_table`. Then add an
`EventBus`-style observer so that every time `export_report` runs, it
publishes an `"export_completed"` event with the format used and row count,
and register two independent listeners (one that logs to a list, one that
prints) to prove they're both notified independently.
