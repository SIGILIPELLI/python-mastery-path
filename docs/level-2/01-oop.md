# 01 · Object-Oriented Programming

Object-oriented programming lets you bundle data and the behavior that acts on
it into a single unit — a class. Level 1 used dictionaries to represent things
like a to-do item; classes give you a more structured, extensible way to model
real-world entities with their own methods and rules.

## Defining a class

```python
class Dog:
    species = "Canis familiaris"   # class attribute, shared by all instances

    def __init__(self, name, age):
        self.name = name           # instance attribute
        self.age = age

    def bark(self):
        return f"{self.name} says woof!"


rex = Dog("Rex", 3)
print(rex.bark())        # Rex says woof!
print(rex.species)       # Canis familiaris
print(Dog.species)       # Canis familiaris — shared across instances
```

`__init__` is the constructor: Python calls it automatically when you create a
new instance. `self` refers to the specific instance being created or acted on.

## Inheritance

A subclass reuses and extends the behavior of a parent class.

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("Subclasses must implement speak()")

    def introduce(self):
        return f"I am {self.name} and I say {self.speak()}"


class Cat(Animal):
    def speak(self):
        return "Meow"


class Cow(Animal):
    def speak(self):
        return "Moo"


for animal in (Cat("Whiskers"), Cow("Bessie")):
    print(animal.introduce())
# I am Whiskers and I say Meow
# I am Bessie and I say Moo
```

## Polymorphism

The loop above is polymorphism in action: the same `introduce()` call behaves
differently depending on the actual (runtime) type of `animal`, because each
subclass provides its own `speak()`.

```python
def make_them_speak(animals):
    for animal in animals:
        print(animal.speak())

make_them_speak([Cat("Tom"), Cow("Milka")])
```

## `super()` — calling the parent implementation

```python
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    def describe(self):
        return f"{self.name} earns {self.salary}"


class Manager(Employee):
    def __init__(self, name, salary, team_size):
        super().__init__(name, salary)   # reuse the parent's __init__
        self.team_size = team_size

    def describe(self):
        base = super().describe()        # reuse the parent's method
        return f"{base} and manages {self.team_size} people"


print(Manager("Priya", 95000, 4).describe())
# Priya earns 95000 and manages 4 people
```

## Dunder (magic) methods

Dunder methods let your objects integrate with Python's built-in syntax
(`print()`, `+`, `==`, `len()`, iteration, and more).

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __len__(self):
        return int((self.x ** 2 + self.y ** 2) ** 0.5)


v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)       # Vector(4, 6)
print(v1 == Vector(1, 2))  # True
print(len(v2))        # 5
```

| Dunder method | Triggered by |
|---------------|--------------|
| `__init__` | creating an instance |
| `__repr__` | `repr(obj)`, debugger/console display |
| `__str__` | `str(obj)`, `print(obj)` |
| `__eq__` | `==` |
| `__lt__` | `<` (and enables `sorted()`) |
| `__len__` | `len(obj)` |
| `__add__` | `+` |
| `__getitem__` | `obj[key]` |
| `__iter__` | `for x in obj` |

## Properties — controlled attribute access

`@property` lets you expose a method as if it were a plain attribute, so you
can validate or compute values without changing the calling code.

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius   # goes through the setter below

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value <= 0:
            raise ValueError("radius must be positive")
        self._radius = value

    @property
    def area(self):
        return 3.14159 * self._radius ** 2


c = Circle(2)
print(c.area)     # 12.56636
c.radius = 5      # goes through the setter, validated
print(c.area)     # 78.53975

try:
    c.radius = -1
except ValueError as e:
    print(e)       # radius must be positive
```

## Class methods and static methods

```python
class Pizza:
    def __init__(self, toppings):
        self.toppings = toppings

    @classmethod
    def margherita(cls):
        """Alternate constructor — a common use of classmethod."""
        return cls(["tomato", "mozzarella", "basil"])

    @staticmethod
    def slice_count(diameter_inches):
        """Doesn't need self or cls — just lives on the class for organization."""
        return diameter_inches // 2


print(Pizza.margherita().toppings)
print(Pizza.slice_count(12))   # 6
```

## How It Actually Works

**A `class` statement is executable code that builds an object.** When the
interpreter reaches `class Dog:`, it:

1. Runs the class body as a mini-scope, collecting every name it defines
   (`species`, `__init__`, `bark`) into a fresh namespace dict.
2. Calls the metaclass — `type` by default — as
   `type("Dog", (object,), namespace)`. That call allocates a new *class
   object* whose `__dict__` is (a mappingproxy over) that namespace, links its
   `__bases__` and computes its `__mro__`.
3. Binds the name `Dog` to that class object. Classes are just objects; `Dog`
   is an instance of `type`.

**Creating an instance:** `Dog("Rex", 3)` calls `type.__call__(Dog, ...)`,
which does `instance = Dog.__new__(Dog)` (allocates a blank object with its own
`__dict__`), then `instance.__init__("Rex", 3)` (your constructor, which fills
that dict), then returns the instance.

**Attribute lookup** (`rex.bark`) is `type.__getattribute__` running a
precise algorithm: check the type's MRO for a *data descriptor* named `bark`;
if none, check the instance's own `__dict__`; if none, check the MRO for a
non-data descriptor or plain class attribute. Functions stored on a class are
*non-data descriptors*: `Dog.__dict__["bark"].__get__(rex, Dog)` returns a
**bound method** that remembers `rex`, which is how `self` gets passed
automatically. `rex.species` misses the instance dict and finds the shared
class attribute — assign `rex.species = ...` and you create an instance-level
entry that shadows it.

`super().describe()` doesn't mean "my parent" — it walks to *the next class
after the current one in the instance's MRO*, which is what makes cooperative
multiple inheritance work.

## Exercise

Model a small library system: a `Book` class with `title`, `author`, and a
`checked_out` boolean; and a `Library` class that holds a list of `Book`
instances and has methods `check_out(title)` and `return_book(title)`. Add
`__repr__` to `Book` so printing a list of books is readable, and a `@property`
on `Library` called `available_titles` that returns titles not checked out.
