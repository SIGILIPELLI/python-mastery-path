# 10 · Project — Weather/Data CLI

A capstone project pulling together everything from Level 2: OOP, comprehensions,
functional-style pipelines, custom exceptions, JSON parsing, and a real
`pytest` test suite. You'll build a command-line tool that fetches current
weather for a city from a free public API, parses the response, and prints a
readable report.

## What you'll build

A CLI that:

- Calls the [Open-Meteo](https://open-meteo.com/) API (no API key required) to
  geocode a city name and fetch its current weather
- Parses the JSON response into a small `WeatherReport` object
- Raises custom exceptions for network failures, unknown cities, or bad data
- Formats a human-readable report, including a simple text "temperature bar"
  built with a comprehension
- Ships with a `pytest` test suite that doesn't require network access

## Project layout

```text
weather_cli/
    weather/
        __init__.py
        errors.py
        client.py
        report.py
        cli.py
    tests/
        test_report.py
        test_client.py
    requirements.txt
```

## requirements.txt

```text
requests==2.31.0
pytest==8.2.0
```

## weather/errors.py — custom exceptions

```python
# weather/errors.py

class WeatherAppError(Exception):
    """Base class for all errors raised by this app."""


class CityNotFoundError(WeatherAppError):
    """Raised when the geocoding API can't find the requested city."""

    def __init__(self, city):
        super().__init__(f"could not find a location matching '{city}'")
        self.city = city


class WeatherServiceError(WeatherAppError):
    """Raised when the weather API request fails or returns bad data."""
```

## weather/client.py — talking to the API

```python
# weather/client.py
import requests

from .errors import CityNotFoundError, WeatherServiceError

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_city(city_name):
    """Return (latitude, longitude, resolved_name) for a city, or raise."""
    try:
        response = requests.get(GEOCODE_URL, params={"name": city_name, "count": 1}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise WeatherServiceError(f"geocoding request failed: {e}") from e

    data = response.json()
    results = data.get("results")
    if not results:
        raise CityNotFoundError(city_name)

    top = results[0]
    return top["latitude"], top["longitude"], top["name"]


def fetch_current_weather(latitude, longitude):
    """Return the raw 'current_weather' dict from Open-Meteo for a location."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
    }
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise WeatherServiceError(f"weather request failed: {e}") from e

    data = response.json()
    current = data.get("current_weather")
    if current is None:
        raise WeatherServiceError("weather response missing 'current_weather'")
    return current
```

Splitting network calls (`client.py`) from parsing/formatting (`report.py`)
keeps the parsing logic testable without ever hitting the real network.

## weather/report.py — parsing and formatting

```python
# weather/report.py
from dataclasses import dataclass

# WMO weather interpretation codes -> human description (subset)
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


@dataclass
class WeatherReport:
    city: str
    temperature_c: float
    windspeed_kmh: float
    weather_code: int

    @property
    def description(self):
        return WEATHER_CODES.get(self.weather_code, "Unknown conditions")

    @property
    def temperature_f(self):
        return self.temperature_c * 9 / 5 + 32

    def temperature_bar(self, width=20, min_temp=-20, max_temp=45):
        """A crude ASCII bar showing where the temperature falls in a range."""
        span = max_temp - min_temp
        filled = int(((self.temperature_c - min_temp) / span) * width)
        filled = max(0, min(width, filled))   # clamp into [0, width]
        return "[" + "#" * filled + "-" * (width - filled) + "]"


def parse_report(city_name, current_weather: dict) -> WeatherReport:
    """Build a WeatherReport from Open-Meteo's raw current_weather dict."""
    try:
        return WeatherReport(
            city=city_name,
            temperature_c=float(current_weather["temperature"]),
            windspeed_kmh=float(current_weather["windspeed"]),
            weather_code=int(current_weather["weathercode"]),
        )
    except (KeyError, TypeError, ValueError) as e:
        from .errors import WeatherServiceError
        raise WeatherServiceError(f"unexpected weather payload: {e}") from e


def format_report(report: WeatherReport) -> str:
    lines = [
        f"Weather for {report.city}",
        f"  Conditions : {report.description}",
        f"  Temperature: {report.temperature_c:.1f}C ({report.temperature_f:.1f}F)  {report.temperature_bar()}",
        f"  Wind speed : {report.windspeed_kmh:.1f} km/h",
    ]
    return "\n".join(lines)
```

## weather/cli.py — command-line entry point

```python
# weather/cli.py
import sys

from .client import geocode_city, fetch_current_weather
from .report import parse_report, format_report
from .errors import WeatherAppError


def run(city_name: str) -> int:
    try:
        latitude, longitude, resolved_name = geocode_city(city_name)
        current = fetch_current_weather(latitude, longitude)
        report = parse_report(resolved_name, current)
    except WeatherAppError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(format_report(report))
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m weather.cli <city name>", file=sys.stderr)
        sys.exit(2)
    city_name = " ".join(sys.argv[1:])
    sys.exit(run(city_name))


if __name__ == "__main__":
    main()
```

## weather/\_\_init\_\_.py

```python
# weather/__init__.py
from .report import WeatherReport, parse_report, format_report
from .errors import WeatherAppError, CityNotFoundError, WeatherServiceError

__all__ = [
    "WeatherReport",
    "parse_report",
    "format_report",
    "WeatherAppError",
    "CityNotFoundError",
    "WeatherServiceError",
]
```

## Running it

```bash
pip install -r requirements.txt
python -m weather.cli London

# Weather for London
#   Conditions : Partly cloudy
#   Temperature: 18.4C (65.1F)  [############--------]
#   Wind speed : 11.2 km/h
```

## tests/test_report.py — pure parsing logic, no network needed

```python
# tests/test_report.py
import pytest

from weather.report import parse_report, format_report, WeatherReport
from weather.errors import WeatherServiceError


def test_parse_report_builds_weather_report():
    raw = {"temperature": 21.5, "windspeed": 9.8, "weathercode": 1}
    report = parse_report("Paris", raw)

    assert isinstance(report, WeatherReport)
    assert report.city == "Paris"
    assert report.temperature_c == 21.5
    assert report.description == "Mainly clear"


def test_parse_report_raises_on_missing_fields():
    with pytest.raises(WeatherServiceError):
        parse_report("Nowhere", {"temperature": 21.5})   # missing windspeed/weathercode


@pytest.mark.parametrize("code, expected", [
    (0, "Clear sky"),
    (63, "Moderate rain"),
    (999, "Unknown conditions"),
])
def test_description_lookup(code, expected):
    report = WeatherReport(city="Test", temperature_c=20, windspeed_kmh=5, weather_code=code)
    assert report.description == expected


def test_temperature_conversion():
    report = WeatherReport(city="Test", temperature_c=0, windspeed_kmh=0, weather_code=0)
    assert report.temperature_f == 32.0


def test_temperature_bar_is_clamped():
    freezing = WeatherReport(city="Test", temperature_c=-100, windspeed_kmh=0, weather_code=0)
    boiling = WeatherReport(city="Test", temperature_c=1000, windspeed_kmh=0, weather_code=0)

    assert freezing.temperature_bar() == "[" + "-" * 20 + "]"
    assert boiling.temperature_bar() == "[" + "#" * 20 + "]"


def test_format_report_includes_city_name():
    report = WeatherReport(city="Berlin", temperature_c=15, windspeed_kmh=3, weather_code=2)
    text = format_report(report)
    assert "Berlin" in text
    assert "Partly cloudy" in text
```

## tests/test_client.py — mocking the network with `monkeypatch`

```python
# tests/test_client.py
import pytest

from weather import client
from weather.errors import CityNotFoundError, WeatherServiceError


class FakeResponse:
    def __init__(self, json_data, status_ok=True):
        self._json_data = json_data
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            import requests
            raise requests.HTTPError("simulated HTTP error")

    def json(self):
        return self._json_data


def test_geocode_city_success(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({"results": [{"latitude": 51.5, "longitude": -0.1, "name": "London"}]})

    monkeypatch.setattr(client.requests, "get", fake_get)
    lat, lon, name = client.geocode_city("London")
    assert (lat, lon, name) == (51.5, -0.1, "London")


def test_geocode_city_not_found(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({"results": []})

    monkeypatch.setattr(client.requests, "get", fake_get)
    with pytest.raises(CityNotFoundError):
        client.geocode_city("Nowhereville")


def test_fetch_current_weather_bad_payload(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(client.requests, "get", fake_get)
    with pytest.raises(WeatherServiceError):
        client.fetch_current_weather(0, 0)
```

`monkeypatch.setattr` swaps out `requests.get` for a fake function during the
test only, so the test suite runs instantly and never depends on network
availability.

## Running the tests

```bash
pytest -v tests/
# tests/test_client.py::test_geocode_city_success PASSED
# tests/test_client.py::test_geocode_city_not_found PASSED
# tests/test_client.py::test_fetch_current_weather_bad_payload PASSED
# tests/test_report.py::test_parse_report_builds_weather_report PASSED
# tests/test_report.py::test_parse_report_raises_on_missing_fields PASSED
# tests/test_report.py::test_description_lookup[0-Clear sky] PASSED
# tests/test_report.py::test_description_lookup[63-Moderate rain] PASSED
# tests/test_report.py::test_description_lookup[999-Unknown conditions] PASSED
# tests/test_report.py::test_temperature_conversion PASSED
# tests/test_report.py::test_temperature_bar_is_clamped PASSED
# tests/test_report.py::test_format_report_includes_city_name PASSED
```

## Stretch goals

- Add a `--units imperial` flag that reports Fahrenheit and mph directly from
  the API instead of converting manually.
- Cache geocoding results for repeated cities in a small JSON file (tying back
  to [Data Formats](05-data-formats.md)).
- Add a 3-day forecast view using Open-Meteo's `daily` parameters.

Completing this project means you're ready for **Level 3 · Advanced**.
