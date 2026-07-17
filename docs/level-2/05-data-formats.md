# 05 · Data Formats (CSV/JSON/XML)

Most real programs spend a lot of time reading and writing data in standard
interchange formats. Python's standard library ships solid support for the
three you'll meet most often: CSV, JSON, and XML.

## CSV — reading

```python
import csv

# sample.csv:
# name,age,city
# Ada,36,London
# Grace,85,New York

with open("sample.csv", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)         # first row
    for row in reader:
        print(row)                # each row is a plain list of strings
# ['Ada', '36', 'London']
# ['Grace', '85', 'New York']
```

## CSV — `DictReader` for named columns

```python
with open("sample.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["age"])   # each row is an OrderedDict/dict
# Ada 36
# Grace 85
```

## CSV — writing

```python
rows = [
    {"name": "Ada", "age": 36, "city": "London"},
    {"name": "Grace", "age": 85, "city": "New York"},
]

with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age", "city"])
    writer.writeheader()
    writer.writerows(rows)
```

Always pass `newline=""` when opening files for `csv` — it prevents extra
blank lines on some platforms.

## JSON — reading and writing

JSON maps very naturally onto Python's built-in types.

```python
import json

data = {
    "name": "Ada Lovelace",
    "born": 1815,
    "contributions": ["Analytical Engine notes", "first algorithm"],
    "active": False,
}

# Python object -> JSON string
text = json.dumps(data, indent=2)
print(text)

# JSON string -> Python object
parsed = json.loads(text)
print(parsed["contributions"][0])   # Analytical Engine notes
```

## JSON — files directly

```python
with open("person.json", "w") as f:
    json.dump(data, f, indent=2)

with open("person.json") as f:
    loaded = json.load(f)
```

## JSON type mapping

| JSON | Python |
|------|--------|
| object | `dict` |
| array | `list` |
| string | `str` |
| number | `int` or `float` |
| `true`/`false` | `True`/`False` |
| `null` | `None` |

## Handling malformed JSON

```python
try:
    json.loads("{not valid json}")
except json.JSONDecodeError as e:
    print(f"invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}")
```

## XML — parsing with `ElementTree`

```python
import xml.etree.ElementTree as ET

xml_text = """
<library>
    <book id="1">
        <title>Structure and Interpretation</title>
        <author>Abelson</author>
    </book>
    <book id="2">
        <title>Fluent Python</title>
        <author>Ramalho</author>
    </book>
</library>
"""

root = ET.fromstring(xml_text)

for book in root.findall("book"):
    title = book.find("title").text
    author = book.find("author").text
    print(f"{title} by {author} (id={book.get('id')})")
# Structure and Interpretation by Abelson (id=1)
# Fluent Python by Ramalho (id=2)
```

## XML — building and writing

```python
library = ET.Element("library")
book = ET.SubElement(library, "book", id="3")
ET.SubElement(book, "title").text = "Automate the Boring Stuff"
ET.SubElement(book, "author").text = "Sweigart"

tree = ET.ElementTree(library)
tree.write("library.xml", encoding="utf-8", xml_declaration=True)
```

## Choosing a format

| Format | Good for | Watch out for |
|--------|----------|----------------|
| CSV | tabular data, spreadsheets | no nested structure, everything is a string |
| JSON | nested data, config, web APIs | no comments, no native dates |
| XML | documents, legacy enterprise systems, attributes + text | more verbose, easy to get parsing wrong |

## Exercise

Given a CSV file of products (`name,price,quantity`), write a script that:
reads it with `csv.DictReader`, converts `price` to `float` and `quantity` to
`int`, computes each product's `total = price * quantity`, and writes the
result as a JSON file — a list of objects with `name` and `total` — sorted by
`total` descending.
