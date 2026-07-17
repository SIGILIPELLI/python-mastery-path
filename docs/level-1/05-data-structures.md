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

## Exercise

Given a list of words, use a dictionary comprehension to build a mapping of
each unique word to its length, then use a set to find which words appear more
than once in the original list.
