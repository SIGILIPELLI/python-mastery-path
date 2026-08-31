"""Paytm Money broker adapter.

Thin, deliberately boring translation layer between `Broker` and Paytm's REST
API. Every call goes through `SessionManager`, so an expired session is
re-established transparently rather than surfacing as a 401 mid-trade.
"""
from __future__ import annotations

import datetime as dt

import httpx

from app.brokers.base import Broker, Candle, OrderResult, Position, Quote
from app.brokers.paytm_auth import SessionManager

BASE = "https://developer.paytmmoney.com"


class PaytmBroker(Broker):
    def __init__(self, sessions: SessionManager | None = None, client: httpx.Client | None = None):
        self.sessions = sessions or SessionManager()
        self._client = client or httpx.Client(base_url=BASE, timeout=20.0)

    def _get(self, path: str, **params) -> dict:
        return self._request("GET", path, params=params)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = {"x-jwt-token": self.sessions.access_token()}
        resp = self._client.request(method, path, headers=headers, **kwargs)
        if resp.status_code == 401:  # session died early; force one refresh
            headers = {"x-jwt-token": self.sessions.refresh()}
            resp = self._client.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ---- market data ------------------------------------------------------
    def history(self, symbol: str, days: int = 120) -> list[Candle]:
        end = dt.date.today()
        start = end - dt.timedelta(days=days * 2)  # pad for weekends/holidays
        payload = self._get(
            "/data/v1/price/chart",
            symbol=symbol,
            interval="D",
            from_date=start.isoformat(),
            to_date=end.isoformat(),
        )
        rows = payload.get("data", payload.get("candles", []))
        return [
            Candle(
                timestamp=dt.datetime.fromisoformat(str(r[0])),
                open=float(r[1]),
                high=float(r[2]),
                low=float(r[3]),
                close=float(r[4]),
                volume=float(r[5]),
            )
            for r in rows
        ][-days:]

    def quote(self, symbol: str) -> Quote:
        payload = self._get("/data/v1/price/live", mode="LTP", pref=f"NSE:{symbol}:EQUITY")
        rows = payload.get("data", [])
        if not rows:
            raise RuntimeError(f"no live quote for {symbol}")
        return Quote(symbol=symbol, last_price=float(rows[0]["last_price"]))

    # ---- account ----------------------------------------------------------
    def positions(self) -> list[Position]:
        payload = self._get("/holdings/v1/positions")
        return [
            Position(
                symbol=r["security_id"] if "security_id" in r else r["symbol"],
                quantity=int(r["net_qty"]),
                average_price=float(r["cost_price"]),
                last_price=float(r["last_traded_price"]),
            )
            for r in payload.get("data", [])
            if int(r.get("net_qty", 0)) != 0
        ]

    def funds(self) -> float:
        payload = self._get("/accounts/v1/funds/summary", config="false")
        return float(payload["data"]["funds_summary"]["available_cash"])

    # ---- execution --------------------------------------------------------
    def place_order(self, symbol: str, side: str, quantity: int, price: float) -> OrderResult:
        payload = self._request(
            "POST",
            "/orders/v1/place/regular",
            json={
                "security_id": symbol,
                "exchange": "NSE",
                "txn_type": "B" if side.upper() == "BUY" else "S",
                "order_type": "LMT",
                "product": "I",
                "price": round(price, 2),
                "quantity": quantity,
                "validity": "DAY",
                "segment": "E",
                "source": "N",
            },
        )
        data = (payload.get("data") or [{}])[0]
        return OrderResult(
            broker_order_id=str(data.get("order_no", "")),
            status=str(data.get("status", "UNKNOWN")),
            filled_price=price,
        )
