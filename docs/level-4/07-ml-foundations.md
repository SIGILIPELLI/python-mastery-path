# 07 · ML Foundations

This module isn't a full machine learning course — it's the minimum
`numpy`/`pandas`/`scikit-learn` fluency a Python engineer needs to understand
ML code, load and prepare data correctly, and train and evaluate a first,
real model.

## Installing

```bash
pip install numpy pandas scikit-learn matplotlib
```

## The core workflow

Every supervised ML project follows roughly the same shape: load data, split
it, train a model on one part, evaluate it on the other.

```text
raw data -> features (X) + target (y) -> train/test split -> fit model -> evaluate
```

## Loading and preparing data

```python
import pandas as pd

df = pd.DataFrame({
    "size_sqft": [850, 1200, 1500, 2000, 2400, 1000, 1800],
    "bedrooms": [2, 3, 3, 4, 4, 2, 3],
    "age_years": [10, 5, 15, 2, 8, 20, 6],
    "price": [210000, 300000, 320000, 450000, 500000, 190000, 380000],
})

X = df[["size_sqft", "bedrooms", "age_years"]]   # features
y = df["price"]                                    # target (what we want to predict)
```

## Train/test split

You never evaluate a model on the same data it was trained on — that would
just measure memorization, not generalization.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42   # random_state makes the split reproducible
)

print(len(X_train), len(X_test))   # 4 3
```

## Training a first model: linear regression

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)   # learns coefficients from the training data

predictions = model.predict(X_test)
print(predictions)

print(dict(zip(X.columns, model.coef_)))   # learned weight for each feature
print(model.intercept_)
```

## Evaluating regression models

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print(f"MAE:  {mae:.0f}")     # average absolute prediction error, in the target's units
print(f"RMSE: {rmse:.0f}")    # penalizes large errors more heavily than MAE
print(f"R^2:  {r2:.3f}")      # fraction of variance explained; 1.0 is perfect
```

## Classification: a simple example

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

clf = DecisionTreeClassifier(max_depth=3, random_state=42)
clf.fit(X_train, y_train)

predictions = clf.predict(X_test)
print(f"accuracy: {accuracy_score(y_test, predictions):.2f}")
print(classification_report(y_test, predictions, target_names=iris.target_names))
```

## Feature scaling

Some algorithms (like those relying on distances) are sensitive to features
being on very different numeric scales — scaling normalizes them.

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # learn mean/std from training data...
X_test_scaled = scaler.transform(X_test)           # ...then apply the SAME transform to test data
```

Always `fit` the scaler only on training data, then `transform` both sets —
fitting on the test set too would leak information from it into training.

## Pipelines — chaining preprocessing and modeling

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression()),
])

pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)
```

A `Pipeline` bundles preprocessing and the model into a single object — calling
`.fit()`/`.predict()` runs every step in order, and it can't accidentally leak
test data into fitting a preprocessing step, since the whole pipeline is
fit once, correctly.

## Cross-validation

A single train/test split can be lucky or unlucky. Cross-validation trains and
evaluates multiple times on different splits, giving a more reliable estimate.

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(pipeline, X, y, cv=5)   # 5-fold cross-validation
print(scores)
print(f"mean accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")
```

## Overfitting vs. underfitting

| Symptom | Training score | Test score | Likely cause |
|---------|-----------------|------------|---------------|
| Underfitting | low | low | model too simple, or too few features |
| Overfitting | high | low | model memorized training data, won't generalize |
| Good fit | high | high (close to training) | model captured real patterns |

```python
train_accuracy = clf.score(X_train, y_train)
test_accuracy = clf.score(X_test, y_test)
print(f"train: {train_accuracy:.3f}, test: {test_accuracy:.3f}")
# a large gap between these two numbers is the classic overfitting signal
```

## Cheat sheet

| Step | scikit-learn tool |
|------|---------------------|
| Split data | `train_test_split(X, y, test_size=..., random_state=...)` |
| Scale features | `StandardScaler().fit_transform(...)` |
| Train a model | `model.fit(X_train, y_train)` |
| Predict | `model.predict(X_test)` |
| Regression metrics | `mean_absolute_error`, `mean_squared_error`, `r2_score` |
| Classification metrics | `accuracy_score`, `classification_report` |
| Chain steps safely | `Pipeline([...])` |
| Robust evaluation | `cross_val_score(model, X, y, cv=5)` |

## How It Actually Works

`model.fit(X_train, y_train)` for `LinearRegression` is solving a concrete numerical
optimization problem, not "learning" in any mystical sense: scikit-learn computes
the coefficients that minimize the sum of squared differences between predicted and
actual `price` values, typically via a **least-squares** solve using linear algebra
(an SVD or normal-equations-based routine from the underlying LAPACK library numpy
wraps) rather than any iterative guessing — for ordinary linear regression there's a
closed-form matrix solution, which is why `.fit()` on this particular model is fast
and deterministic given the same data. The `model.coef_` values are literally the
entries of the solved coefficient vector, one weight per feature column in `X`,
representing how much the prediction changes per unit change in that feature holding
the others fixed.

`train_test_split(..., random_state=42)` doesn't do anything model-specific — it
shuffles row indices using a seeded pseudorandom number generator and partitions
them into two groups at the requested ratio. The seed matters mechanically because a
PRNG is deterministic given its seed: the exact same `random_state` value always
produces the exact same shuffle order on the exact same input, which is why fixing
it makes an experiment reproducible across runs and across machines, while leaving
it unset means a different random split (and slightly different resulting metrics)
every time.

`StandardScaler().fit(X_train)` computes and stores the mean and standard deviation
of *each column* of `X_train` as internal attributes; `.transform(X)` then applies
`(x - mean) / std` element-wise to whatever data you pass it, using those *stored*
values rather than recomputing them from `X` itself. This is precisely the
mechanical reason for "fit only on training data, transform both": if you called
`.fit_transform()` on the test set too, the mean/std used to scale it would be
computed *including* test-set values, meaning information about the exact
distribution of data the model will be "evaluated" on has leaked into the
preprocessing step — an optimistic bias in the resulting metric that wouldn't
reproduce on genuinely new, unseen data in production. A `Pipeline` structurally
prevents this mistake by construction: calling `pipeline.fit(X_train, y_train)`
internally calls `.fit_transform()` on each preprocessing step in sequence but
`.transform()` only (never re-fitting) on `pipeline.predict(X_test)`, so the same
learned mean/std automatically get reused correctly with no way to accidentally
call the wrong method on the wrong split.

`cross_val_score(pipeline, X, y, cv=5)` partitions the *entire* dataset into 5
roughly equal folds, then runs 5 separate full fit/evaluate cycles, each time
holding out one fold as the test set and training fresh on the other four — a
brand-new `Pipeline` (with brand-new fitted scaler and model) is fit each time, none
sharing state with another fold's run. Averaging the 5 resulting scores gives a much
more reliable performance estimate than one split because it's no longer sensitive
to which particular rows happened to land in the one test set a single
`train_test_split` would have produced — a lucky or unlucky split is averaged out
across five independent measurements.

## Exercise

Using the `iris` dataset, build a `Pipeline` with a `StandardScaler` and a
`LogisticRegression` classifier. Evaluate it with 5-fold `cross_val_score`,
then fit it on a train split and print a full `classification_report` on the
held-out test split. Finally, deliberately train a `DecisionTreeClassifier`
with no `max_depth` limit and compare its train vs. test accuracy to the
depth-limited version from this module to observe overfitting directly.
