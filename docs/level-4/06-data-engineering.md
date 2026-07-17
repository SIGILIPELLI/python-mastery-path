# 06 · Data Engineering

Data engineering is about moving and reshaping data reliably: extracting it
from sources, transforming it into a usable shape, and loading it somewhere
useful (a database, a file, a dashboard). `pandas` and `numpy` are the core
tools for this in the Python ecosystem.

## Installing

```bash
pip install pandas numpy
```

## `numpy` — fast numerical arrays

`numpy` arrays are fixed-type and stored contiguously in memory, which makes
vectorized operations on them far faster than equivalent pure-Python loops.

```python
import numpy as np

prices = np.array([19.99, 5.50, 3.25, 42.00])
quantities = np.array([2, 10, 5, 1])

totals = prices * quantities            # element-wise multiplication, no loop needed
print(totals)                            # [ 39.98  55.    16.25  42.  ]
print(totals.sum())                       # 153.23
print(totals.mean(), totals.std())        # average and standard deviation

matrix = np.array([[1, 2], [3, 4]])
print(matrix.T)                           # transpose
print(matrix @ matrix)                     # matrix multiplication
```

## `pandas` — the `DataFrame`

A `DataFrame` is a labeled, 2-dimensional table — think "a spreadsheet you can
script."

```python
import pandas as pd

data = {
    "product": ["Book", "Pen", "Notebook", "Book"],
    "price": [12.50, 1.50, 5.00, 12.50],
    "quantity": [3, 20, 8, 1],
}
df = pd.DataFrame(data)

print(df)
#     product  price  quantity
# 0      Book  12.50         3
# 1       Pen   1.50        20
# 2  Notebook   5.00         8
# 3      Book  12.50         1

print(df.dtypes)
print(df.describe())    # count, mean, std, min, max, quartiles for numeric columns
```

## Reading and writing common formats

```python
df = pd.read_csv("sales.csv")
df.to_csv("output.csv", index=False)

df = pd.read_json("data.json")
df.to_json("output.json", orient="records", indent=2)

df = pd.read_excel("report.xlsx")     # requires: pip install openpyxl
```

## Selecting and filtering

```python
print(df["price"])                       # a single column (a Series)
print(df[["product", "price"]])            # multiple columns
print(df[df["quantity"] > 5])               # filter rows by a boolean condition
print(df.loc[df["product"] == "Book"])      # filter by label-based indexing
print(df.iloc[0])                            # the first row by position
```

## Adding and transforming columns

```python
df["total"] = df["price"] * df["quantity"]

df["price_category"] = df["price"].apply(
    lambda p: "expensive" if p > 10 else "cheap"
)

print(df)
```

## Grouping and aggregating

```python
grouped = df.groupby("product")["total"].sum()
print(grouped)
# product
# Book        50.0
# Notebook    40.0
# Pen         30.0

summary = df.groupby("product").agg(
    total_revenue=("total", "sum"),
    avg_price=("price", "mean"),
    orders=("product", "count"),
)
print(summary)
```

## Handling missing data

```python
df_with_gaps = pd.DataFrame({"a": [1, None, 3], "b": [None, 2, 3]})

print(df_with_gaps.isna())              # boolean mask of missing values
print(df_with_gaps.dropna())             # drop any row containing a missing value
print(df_with_gaps.fillna(0))            # replace missing values with 0
print(df_with_gaps["a"].fillna(df_with_gaps["a"].mean()))   # fill with the column mean
```

## Merging/joining data

```python
orders = pd.DataFrame({"order_id": [1, 2, 3], "customer_id": [1, 2, 1]})
customers = pd.DataFrame({"customer_id": [1, 2], "name": ["Ada", "Grace"]})

merged = orders.merge(customers, on="customer_id", how="left")
print(merged)
#    order_id  customer_id  name
# 0         1            1   Ada
# 1         2            2 Grace
# 2         3            1   Ada
```

## Designing a small ETL pipeline

A basic Extract-Transform-Load pipeline, structured as small, testable
functions.

```python
import pandas as pd

def extract(csv_path: str) -> pd.DataFrame:
    """Extract: read raw sales data from a CSV file."""
    return pd.read_csv(csv_path)


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform: clean and enrich the raw data."""
    df = df.dropna(subset=["product", "price", "quantity"])
    df = df[df["quantity"] > 0]                     # drop invalid rows
    df["total"] = df["price"] * df["quantity"]
    return df.groupby("product", as_index=False).agg(
        total_revenue=("total", "sum"),
        units_sold=("quantity", "sum"),
    )


def load(df: pd.DataFrame, output_path: str) -> None:
    """Load: write the final, aggregated result somewhere durable."""
    df.to_csv(output_path, index=False)


def run_pipeline(input_path: str, output_path: str) -> None:
    raw = extract(input_path)
    clean = transform(raw)
    load(clean, output_path)
    print(f"processed {len(raw)} rows into {len(clean)} product summaries")


if __name__ == "__main__":
    run_pipeline("sales.csv", "sales_summary.csv")
```

Splitting `extract`/`transform`/`load` into separate functions makes each
stage independently testable — `transform` in particular can be tested with
an in-memory `DataFrame`, no file I/O required.

## Cheat sheet

| Task | Code |
|------|------|
| Read CSV/JSON/Excel | `pd.read_csv/json/excel(path)` |
| Filter rows | `df[df["col"] > value]` |
| New column from existing ones | `df["new"] = df["a"] * df["b"]` |
| Group and summarize | `df.groupby("col").agg(...)` |
| Join two tables | `df1.merge(df2, on="key", how="left")` |
| Handle missing data | `df.dropna()` / `df.fillna(value)` |

## Exercise

Build the ETL pipeline above into a real script with a `tests/test_transform.py`
file that constructs a small in-memory `DataFrame` with a missing value, a
zero-quantity row, and two rows for the same product — and asserts the
transformed output drops the bad rows and correctly sums the duplicate
product's revenue and units.
