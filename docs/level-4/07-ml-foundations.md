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

## Exercise

Using the `iris` dataset, build a `Pipeline` with a `StandardScaler` and a
`LogisticRegression` classifier. Evaluate it with 5-fold `cross_val_score`,
then fit it on a train split and print a full `classification_report` on the
held-out test split. Finally, deliberately train a `DecisionTreeClassifier`
with no `max_depth` limit and compare its train vs. test accuracy to the
depth-limited version from this module to observe overfitting directly.
