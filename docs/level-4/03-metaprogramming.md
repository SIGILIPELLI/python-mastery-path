# 03 · Metaprogramming

Metaprogramming means writing code that manipulates code or classes as data —
inspecting, generating, or modifying them at runtime. Level 3 introduced
metaclasses briefly; this module goes deeper, covers the more commonly used
`__init_subclass__` hook, and touches on generating code dynamically.

## Metaclasses, deep dive

Every class is an instance of a metaclass — by default, `type`. Defining a
custom metaclass lets you hook into the class creation process itself, not
just instance creation.

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        print(f"creating class {name}")
        cls = super().__new__(mcs, name, bases, namespace)
        return cls

    def __init__(cls, name, bases, namespace, **kwargs):
        print(f"initializing class {name}")
        super().__init__(name, bases, namespace)


class MyClass(metaclass=Meta):
    pass

# output at import time, before any instance exists:
# creating class MyClass
# initializing class MyClass
```

`__new__` builds the class object; `__init__` initializes it further — the
same split that exists for regular instances, just one level up.

## A practical metaclass: auto-registering plugins

```python
class PluginMeta(type):
    registry = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:   # skip the base class itself
            PluginMeta.registry[name] = cls
        return cls


class Plugin(metaclass=PluginMeta):
    pass


class CSVExporter(Plugin):
    def export(self, data):
        return ",".join(map(str, data))


class JSONExporter(Plugin):
    def export(self, data):
        import json
        return json.dumps(data)


print(PluginMeta.registry)
# {'CSVExporter': <class '__main__.CSVExporter'>, 'JSONExporter': <class '__main__.JSONExporter'>}

exporter_cls = PluginMeta.registry["CSVExporter"]
print(exporter_cls().export([1, 2, 3]))   # 1,2,3
```

Every subclass of `Plugin` is registered automatically the moment it's
defined — no manual registration call required anywhere.

## `__init_subclass__` — the simpler alternative

For most "do something whenever a subclass is created" use cases,
`__init_subclass__` (a regular classmethod hook, no metaclass required) is
simpler and preferred.

```python
class Plugin:
    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[cls.__name__] = cls


class CSVExporter(Plugin):
    def export(self, data):
        return ",".join(map(str, data))


class JSONExporter(Plugin):
    def export(self, data):
        import json
        return json.dumps(data)


print(Plugin.registry)
# {'CSVExporter': <class '__main__.CSVExporter'>, 'JSONExporter': <class '__main__.JSONExporter'>}
```

Same result as the metaclass version above, with far less ceremony — reach
for `__init_subclass__` first, and only use a full metaclass when you need to
change something about class *creation itself* (like validating the
namespace dict before the class exists, which `__init_subclass__` runs too
late for).

## When to actually reach for a metaclass

| Need | Use |
|------|-----|
| React when a subclass is defined | `__init_subclass__` |
| Validate/modify attributes before the class object exists | metaclass `__new__` |
| Change what `isinstance()`/`issubclass()` report | metaclass `__instancecheck__`/`__subclasscheck__` |
| Most everyday "framework" behavior (ORMs, plugin systems, etc.) | `__init_subclass__` first; metaclass only if that's insufficient |

Django's ORM and SQLAlchemy's declarative base both use metaclasses
internally — it's a real, load-bearing tool in production frameworks, just
one that's easy to reach for too early.

## `__class_getitem__` — supporting `MyClass[int]` syntax

```python
class Container:
    def __init__(self, items):
        self.items = items

    def __class_getitem__(cls, item):
        # lets you write Container[int] for documentation/typing purposes
        return cls


IntContainer = Container[int]   # works like a type hint annotation
```

## Dynamic class and function creation

```python
# creating a class dynamically with type(name, bases, namespace)
Point = type("Point", (), {
    "__init__": lambda self, x, y: (setattr(self, "x", x), setattr(self, "y", y)),
    "__repr__": lambda self: f"Point({self.x}, {self.y})",
})

p = Point(1, 2)
print(p)   # Point(1, 2)

# generating a function from a string with exec (use sparingly!)
namespace = {}
exec("def add(a, b): return a + b", namespace)
add = namespace["add"]
print(add(2, 3))   # 5
```

`exec`-based code generation is exactly how libraries like `dataclasses` and
`attrs` build fast `__init__`/`__repr__` methods under the hood — but it's
risky and hard to debug in application code, so reach for it only when
building framework-level tooling, never for ordinary business logic.

## Inspecting objects at runtime

```python
import inspect

class Greeter:
    def greet(self, name: str) -> str:
        return f"Hello, {name}"


print(inspect.signature(Greeter.greet))          # (self, name: str) -> str
print(inspect.getsource(Greeter.greet))           # prints the actual source code
print([m for m in dir(Greeter) if not m.startswith("_")])   # ['greet']
```

## Cheat sheet

| Tool | Purpose |
|------|---------|
| `__init_subclass__` | react to subclass creation (preferred, simpler) |
| `metaclass=` / `type.__new__` | full control over class construction |
| `type(name, bases, ns)` | build a class dynamically at runtime |
| `exec(code, namespace)` | generate and run code from a string (framework-level only) |
| `inspect` module | introspect signatures, source, members at runtime |

## Exercise

Build a small validation framework using `__init_subclass__`: a base class
`Model` that auto-registers every subclass by name (like the plugin registry
above), plus a class-level `fields: dict[str, type]` declared on each
subclass. Give `Model.__init__` a generic implementation that validates
`**kwargs` against `fields` (raising `TypeError` on an unknown field or wrong
type) and sets them as attributes — so subclasses only need to declare
`fields`, never write their own `__init__`.
