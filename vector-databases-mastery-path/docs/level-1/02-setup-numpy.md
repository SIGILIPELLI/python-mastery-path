---
description: "A vector is just a NumPy array — np.linalg.norm gives you its length, and that single function underlies almost every similarity metric you'll use in this course."
---

# 02 · Setup: Python, NumPy & Your First Vectors

## Install Python and NumPy

You'll need Python 3.9+ for this course.

```bash
# macOS (Homebrew)
brew install python

# Ubuntu/Debian
sudo apt install python3 python3-pip

# Windows
# Download from https://www.python.org/downloads/
```

Create a virtual environment and install NumPy:

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install numpy
```

Verify it:

```python
import numpy as np
print(np.__version__)
```

## Creating your first vectors

A vector in this course is just a 1-dimensional NumPy array of floats:

```python
import numpy as np

v = np.array([0.2, 0.9, -0.1])
print(v)          # [ 0.2  0.9 -0.1]
print(v.shape)     # (3,)
print(v.dtype)     # float64
```

Real embedding models produce vectors with hundreds of dimensions (384, 768,
1536 are common sizes), but the math is identical whether you have 3 numbers
or 1536 — NumPy doesn't care.

## Basic vector operations

```python
a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])

a + b              # array([5., 7., 9.])   element-wise addition
a - b              # array([-3., -3., -3.])
a * 2.0            # array([2., 4., 6.])   scalar multiply
a * b              # array([4., 10., 18.]) element-wise multiply (NOT dot product)
```

## Magnitude (norm)

The **magnitude** (or **norm**, or **length**) of a vector tells you how far
it is from the origin. For a 3D vector `[x, y, z]` it's the familiar
Pythagorean formula extended to N dimensions:

```
‖v‖ = sqrt(v₁² + v₂² + ... + vₙ²)
```

```python
v = np.array([3.0, 4.0])
magnitude = np.linalg.norm(v)
print(magnitude)   # 5.0   (3-4-5 right triangle)
```

`np.linalg.norm` works for any number of dimensions:

```python
v = np.array([0.2, 0.9, -0.1, 0.4, -0.6])
print(np.linalg.norm(v))   # sqrt(0.04+0.81+0.01+0.16+0.36) ≈ 1.095
```

You'll use this constantly: normalizing a vector (dividing it by its own
magnitude) produces a **unit vector** — same direction, length exactly 1 —
which is the basis for cosine similarity in the next lesson.

```python
def normalize(v):
    return v / np.linalg.norm(v)

unit = normalize(np.array([3.0, 4.0]))
print(unit)                      # [0.6 0.8]
print(np.linalg.norm(unit))      # 1.0
```

## Representing toy "documents" as vectors

Before you generate real embeddings in Lesson 5, it helps to hand-craft a
tiny dataset so you can reason about the numbers directly. Imagine a
4-dimensional space where each dimension loosely tracks a theme —
`[animals, technology, food, sports]`:

```python
documents = {
    "doc1": np.array([0.9, 0.1, 0.0, 0.0]),   # about animals
    "doc2": np.array([0.8, 0.2, 0.1, 0.0]),   # also about animals, slightly tech
    "doc3": np.array([0.0, 0.9, 0.1, 0.0]),   # about technology
    "doc4": np.array([0.0, 0.0, 0.1, 0.9]),   # about sports
}

for name, vec in documents.items():
    print(name, "magnitude:", round(np.linalg.norm(vec), 3))
```

Real models never hand you interpretable dimensions like this — but keeping
this toy dataset around for the next two lessons will let you verify that
your distance and similarity code behaves the way you expect before you
point it at opaque, 384-number real embeddings.

## Exercise

Create three vectors of your own representing fictional documents. Use
`np.linalg.norm` to compute each one's magnitude, then normalize all three
into unit vectors and confirm each normalized vector has magnitude `1.0`
(allow for tiny floating-point error, e.g. `0.9999999999999998`). Print a
table of document name → original magnitude → normalized magnitude.
