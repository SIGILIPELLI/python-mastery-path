# 05 · Core Data Structures

## Lists — ordered, mutable

```python
fruits = ["apple", "banana", "cherry"]

fruits.append("date")        # add to end
fruits.insert(0, "avocado")  # insert at index
fruits.remove("banana")      # remove by value
last = fruits.pop()           # remove & return last item

print(fruits[0])       # first item
print(fruits[-1])      # last item
print(fruits[1:3])     # slice: index 1 up to (not including) 3
print(len(fruits))

squares = [n * n for n in range(5)]  # list comprehension
# [0, 1, 4, 9, 16]
```

## Tuples — ordered, immutable

```python
point = (3, 4)
x, y = point   # unpacking

# Tuples are hashable if their contents are, so they can be dict keys / set members
locations = {(0, 0): "origin", (1, 1): "corner"}
```

## Dictionaries — key/value pairs

```python
person = {"name": "Ada", "age": 30}

person["email"] = "ada@example.com"   # add/update
age = person.get("age", 0)             # safe lookup with default
person.pop("age", None)                 # remove key safely

for key, value in person.items():
    print(key, value)

squared_map = {n: n * n for n in range(5)}  # dict comprehension
```

## Sets — unordered, unique elements

```python
a = {1, 2, 3}
b = {2, 3, 4}

print(a | b)   # union: {1, 2, 3, 4}
print(a & b)   # intersection: {2, 3}
print(a - b)   # difference: {1}
print(3 in a)  # membership test: True
```

## Choosing the right structure

| Need | Use |
|------|-----|
| Ordered, allow duplicates, will change | `list` |
| Ordered, allow duplicates, won't change | `tuple` |
| Fast lookup by unique key | `dict` |
| Unique items, fast membership tests | `set` |

## How It Actually Works

Each of these types is a different memory layout with different performance
consequences:

- **`list`** is a *dynamic array of pointers* — a contiguous C block holding
  `PyObject*` values, plus a length and a capacity. Indexing is O(1) pointer
  arithmetic. `append` is *amortized* O(1): when the array fills, CPython
  allocates a bigger block (growth factor ~1.125, over-allocating on purpose)
  and copies the pointers over. `insert(0, x)` and `pop(0)` are O(n) because
  every following pointer must shift.
- **`tuple`** is the same pointer array but fixed-size and allocated once, so
  it's slightly smaller and lets CPython cache/reuse small tuples. Immutability
  is what makes it hashable (if its contents are).
- **`dict`** is an *open-addressing hash table*. A key's `__hash__` is masked
  to an index; on collision CPython probes other slots by a perturbation
  sequence. Since 3.6 the layout is "compact": a dense insertion-ordered array
  of `(hash, key, value)` entries plus a sparse index array of positions —
  that's why dicts preserve insertion order *and* use less memory. Average
  lookup is O(1); it triggers a resize (rehash of all entries) when about
  two-thirds full.
- **`set`** is a hash table with keys only, same probing scheme. `x in a_set`
  is O(1) average; `x in a_list` is O(n).

Everything hinges on hashing: `dict`/`set` keys must be hashable (implement
`__hash__` and not mutate in a way that changes it), which is why lists can't
be keys but tuples of immutables can. `hash(x) == hash(y)` for equal objects
is a required invariant — break it and lookups silently fail.

## Exercise

Given a list of words, use a dictionary comprehension to build a mapping of
each unique word to its length, then use a set to find which words appear more
than once in the original list.
