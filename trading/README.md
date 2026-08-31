# Multi-Agent Auto Trading (Paytm Money)

A cloud-resident trading service where several independent agents analyse the
same tape, a coordinator turns their disagreement into at most one decision per
symbol, and a risk agent holds a veto over all of them.

---

## Read this before anything else

**"Log in once and never again" is not achievable against any Indian broker.**
SEBI requires an interactive login per session, and Paytm Money access tokens
expire at the end of every trading day. Anyone promising otherwise is either
wrong or storing your session in a way that will break.

What this app does instead:

1. You onboard **once** — API key/secret, login id, password, TOTP seed.
2. Everything is Fernet-encrypted before it touches the database. The key lives
   only in the platform's secret store, so a stolen DB file is useless.
3. At **08:45 IST every weekday** a scheduled job replays that login headlessly
   (password → TOTP from the stored seed → request token → access token).
4. If that ever fails, trading **halts** and `/health` reports
   `needs_manual_login: true`. It never trades on a stale session.

From your side it is one login, ever. Under the hood it is a fresh, legal
session each day.

**Second warning:** `DRY_RUN=true` is the default and it is there for a reason.
The paper broker's price series is synthetic — a backtest against it measures
the code, not the strategy. Run against live Paytm data in dry-run for weeks
and read `/orders` before you ever set `DRY_RUN=false`. This is not financial
advice, and you can lose money.

---

## Architecture

```
                  ┌──────────────── analyst fleet ────────────────┐
   market data →  │ momentum  mean-reversion  breakout  vol-regime│
                  └───────────────────────┬───────────────────────┘
                                          │ Signal(action, confidence, why)
                                  ┌───────▼────────┐
                                  │  Coordinator   │  weighted consensus
                                  └───────┬────────┘  + agreement + dissent damping
                                          │ Decision
                                  ┌───────▼────────┐
                                  │   RiskAgent    │  ATR sizing, hard caps, kill switch
                                  └───────┬────────┘
                                          │ approved quantity
                                  ┌───────▼────────┐
                                  │    Engine      │ → Broker (paper | paytm)
                                  └────────────────┘
```

Every layer is one-way. No agent can reach `place_order` without passing risk.

### The agents

| Agent | Method | Weight |
|---|---|---|
| `momentum` | 20/50-day moving-average separation | 1.2 |
| `mean_reversion` | 20-day z-score + RSI(14), fades extremes | 1.0 |
| `breakout` | 55-day Donchian channel break | 0.9 |
| `volatility_regime` | 10d vs 60d realised vol; risk-off veto | 0.8 |

They are chosen to be *uncorrelated in method* — momentum and mean reversion
are literal opposites — so agreement between them carries information a single
model does not have.

**Consensus rule:** weighted mean of signed confidences, then two guards —
a trade needs at least two agents pointing the same way (no single loud agent
can move the book), and the consensus is scaled by how split the fleet is.

### Risk controls

- Position size from ATR: fixed rupee risk to a 2×ATR stop, so a jumpy stock
  gets fewer shares than a calm one.
- Hard caps applied *after* sizing: `MAX_POSITION_PCT`, `MAX_OPEN_POSITIONS`,
  cash on hand.
- `MAX_DAILY_LOSS_PCT` is a kill switch checked before every order.
- No shorting, no pyramiding, limit orders only.

---

## Run it

```bash
cd trading
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
# generate the vault key
.venv/bin/python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"
# paste it as VAULT_KEY, set ADMIN_TOKEN, then:
.venv/bin/uvicorn app.main:app --reload
```

Tests: `.venv/bin/python -m pytest -q` (24 tests, no network).

### Deploy

```bash
fly launch --no-deploy
fly secrets set VAULT_KEY=... ADMIN_TOKEN=... BROKER=paytm DRY_RUN=true
fly volumes create trader_data --size 1
fly deploy
```

Or `docker compose up -d`. Either way the `data/` volume must persist — it
holds the encrypted vault and the audit trail.

### One-time onboarding

```bash
curl -X POST https://your-app/auth/onboard \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' \
  -d '{"api_key":"...","api_secret":"...","login_id":"...",
       "password":"...","totp_secret":"BASE32SEED"}'
```

That is the last time you supply credentials.

---

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | – | status, dry-run flag, `needs_manual_login` |
| POST | `/auth/onboard` | admin | one-time credential onboarding |
| POST | `/auth/refresh` | admin | force a re-auth now |
| POST | `/auth/request-token` | admin | manual fallback if headless login breaks |
| POST | `/run` | admin | run one agent pass immediately |
| GET | `/report` | – | last pass: decisions, orders, skips, errors |
| GET | `/positions` | – | live positions with P&L |
| GET | `/orders` | – | order history with the rationale for each |
| GET | `/events` | – | audit log |
| GET | `/backtest/{symbol}` | admin | walk-forward backtest on the live agents |

Every order stores the full agent breakdown that produced it, so any trade can
be explained months later.

## Schedule (IST)

- **08:45** headless re-auth
- **09:15–15:15, every 15 min, weekdays** agent pass
- **15:25** end-of-day log

## Verify before going live

`Endpoints` in `app/brokers/paytm_auth.py` and the paths in `app/brokers/paytm.py`
are Paytm's documented routes, but Paytm has revised them before. Check them
against <https://developer.paytmmoney.com> and run a dry-run day before
flipping `DRY_RUN=false`.
