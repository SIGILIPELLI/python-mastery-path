# 01 · Advanced OOP

Level 2 covered classes, inheritance, and dunder methods. This module goes
further: formal interfaces with abstract base classes, composing behavior with
mixins, and a first look at metaclasses — the mechanism that creates classes
themselves.

## Abstract base classes (ABCs)

An ABC defines a contract: subclasses *must* implement certain methods, or
Python refuses to let you instantiate them. This catches missing
implementations at object-creation time instead of failing later when the
missing method is finally called.

```python
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def charge(self, amount):
        """Charge the given amount. Must be implemented by subclasses."""

    @abstractmethod
    def refund(self, amount):
        """Refund the given amount. Must be implemented by subclasses."""

    def receipt(self, amount):
        # concrete methods can still live on an ABC and be shared by all subclasses
        return f"Charged {amount} via {type(self).__name__}"


class CreditCard(PaymentMethod):
    def charge(self, amount):
        return f"Charging ${amount} to credit card"

    def refund(self, amount):
        return f"Refunding ${amount} to credit card"


try:
    PaymentMethod()   # TypeError: Can't instantiate abstract class
except TypeError as e:
    print(e)

card = CreditCard()
print(card.charge(50))
print(card.receipt(50))
```

If `CreditCard` forgot to implement `refund`, instantiating it would raise
`TypeError: Can't instantiate abstract class CreditCard with abstract method refund`
— caught immediately, rather than a confusing `AttributeError` deep in
production.

## Mixins — composing reusable behavior

A mixin is a small class meant to be combined with others via multiple
inheritance, adding one focused piece of behavior rather than representing a
complete "is-a" relationship.

```python
class JSONSerializableMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)


class ComparableByNameMixin:
    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name


class Product(JSONSerializableMixin, ComparableByNameMixin):
    def __init__(self, name, price):
        self.name = name
        self.price = price


p1 = Product("Widget", 9.99)
p2 = Product("Gadget", 19.99)

print(p1.to_json())         # {"name": "Widget", "price": 9.99}
print(sorted([p1, p2]))      # sorted using ComparableByNameMixin's __lt__
```

## Method resolution order (MRO)

When a class inherits from multiple parents, Python needs a deterministic
order to search for methods — the MRO, computed with the C3 linearization
algorithm.

```python
class A:
    def greet(self):
        return "A"

class B(A):
    def greet(self):
        return "B -> " + super().greet()

class C(A):
    def greet(self):
        return "C -> " + super().greet()

class D(B, C):
    def greet(self):
        return "D -> " + super().greet()


print(D().greet())          # D -> B -> C -> A
print([cls.__name__ for cls in D.__mro__])
# ['D', 'B', 'C', 'A', 'object']
```

Each `super().greet()` call moves to the *next* class in the MRO — not
necessarily straight to the immediate parent — which is what lets `B` and `C`
both run exactly once even though both inherit from `A`.

## Properties, revisited: computed & cached attributes

```python
from functools import cached_property

class Report:
    def __init__(self, rows):
        self.rows = rows

    @cached_property
    def total(self):
        print("computing total...")   # only prints once
        return sum(self.rows)


report = Report([10, 20, 30])
print(report.total)   # computing total... / 60
print(report.total)   # 60 (cached — no recomputation)
```

`@cached_property` (from `functools`) computes the value once on first access
and stores it on the instance, useful for expensive derived values that don't
change.

## A first look at metaclasses

A class is itself an instance of something — normally `type`. A metaclass lets
you customize how classes get built, e.g. validating their structure or
auto-registering subclasses.

```python
class ValidatingMeta(type):
    def __new__(mcs, name, bases, namespace):
        # runs once, when the CLASS (not instance) is created
        if "required_field" not in namespace and bases:
            raise TypeError(f"{name} must define 'required_field'")
        return super().__new__(mcs, name, bases, namespace)


class Base(metaclass=ValidatingMeta):
    required_field = None   # satisfies the base class itself


class Good(Base):
    required_field = "present"


try:
    class Bad(Base):
        pass   # missing required_field
except TypeError as e:
    print(e)   # Bad must define 'required_field'
```

Metaclasses are a deep topic — Level 4's
[Metaprogramming](../level-4/03-metaprogramming.md) module covers them (and
the more commonly used `__init_subclass__` alternative) in much more depth.
For now, recognize that `class Foo(metaclass=Something)` hooks into how the
class object itself gets built.

## Cheat sheet

| Concept | Purpose |
|---------|---------|
| `ABC` + `@abstractmethod` | enforce a required interface |
| Mixin | share one focused behavior across unrelated classes |
| MRO (`ClassName.__mro__`) | the order Python searches for attributes/methods |
| `@cached_property` | compute an expensive attribute once, reuse it |
| `metaclass=` | customize how classes themselves are constructed |

## How It Actually Works

An ABC's enforcement isn't checked at method-call time — it's checked at
**instantiation time**, and the mechanism is a metaclass. `ABC` is built on
`ABCMeta`, a subclass of `type`; `@abstractmethod` just tags a function object with
a `__isabstractmethod__ = True` attribute. When a class body finishes executing,
`ABCMeta.__new__` scans the resulting namespace (and inherited members) for anything
still carrying that flag and stores the set of unimplemented names on the class as
`__abstractmethods__`. `object.__new__` (called during instantiation) checks that set
and raises `TypeError` immediately if it's non-empty — which is exactly why
`PaymentMethod()` fails before `__init__` ever runs, and why a subclass that
overrides every abstract method with a concrete one becomes instantiable again: its
own `__abstractmethods__` computes to empty.

The MRO for `class D(B, C)` is not "depth-first left-to-right" (the old, broken
classic algorithm) — CPython computes it with **C3 linearization**: merge the MROs
of `B` and `C` plus the list `[B, C]` itself, taking the head of the first list that
doesn't appear in the tail of any other list, repeating until nothing's left. This
guarantees each ancestor appears exactly once and *before* its own parents, and that
the order respects each base's own local precedence — that's why `D → B → C → A`,
not `D → B → A → C → A`. `super().greet()` doesn't call "the parent" — it looks up
`type(self).__mro__`, finds the calling class's position in it, and calls the *next*
entry — which is why `B.greet` and `C.greet` both run exactly once even though both
ultimately inherit from `A`: each `super()` call advances one shared position along
one shared list, not down two independent lineages.

`@cached_property` is a **non-data descriptor** (it defines `__get__` but not
`__set__`), which matters specifically because of attribute lookup priority: a
non-data descriptor is checked only if the instance's own `__dict__` doesn't already
have that name. The first access to `report.total` runs your function, computes the
result, and then manually writes `self.__dict__["total"] = 60` — after that, ordinary
attribute lookup finds `total` sitting directly in the instance's `__dict__` and
never consults the descriptor's `__get__` again, which is the entire caching
mechanism (and why the class needs a real, writable instance `__dict__` to work at
all).

Finally, `class Bad(Base): ...` triggers `ValidatingMeta.__new__` before `Bad` even
exists as an object: the `class` statement itself compiles to a call to the
metaclass — `ValidatingMeta("Bad", (Base,), namespace)` — and only if that call
returns successfully does the name `Bad` get bound. Raising `TypeError` inside
`__new__` means the class object is never created at all, not merely rejected after
the fact.

## Exercise

Define an ABC `Shape` with abstract methods `area()` and `perimeter()`, plus a
concrete method `describe()` that returns a formatted string using both. Add a
`RoundingMixin` that overrides `describe()` to round its output to 2 decimal
places before delegating to the parent's version via `super()`. Implement
`Rectangle` and `Circle` subclasses that combine `Shape` with
`RoundingMixin`, and confirm instantiating a `Shape` directly raises
`TypeError`.
