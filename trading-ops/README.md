# Trading-ops virtual employee

Oversight layer for the live Paytm Money trading bot at
`~/Desktop/my_claude_project/trading_bot`. This does **not** contain any
trading logic — the bot already has its own multi-agent strategy, risk
manager, and daily-loss circuit breaker. This is process supervision,
alerting, and reporting on top of it.

## What's running

- **`supervisor.py`** — via launchd (`com.vremployee.trading-supervisor`),
  every 2 minutes:
  - Detects if `main.py --mode live` is down during market hours.
  - Distinguishes a manual stop (Ctrl-C/SIGTERM — logged by the bot itself)
    from a crash. Only crashes trigger auto-restart.
  - Auto-restarts by piping the bot's own `"YES I UNDERSTAND"` live-mode
    confirmation — **this bypasses that manual safety brake on every
    restart**, by explicit user choice (they were shown the trade-off:
    alert-and-wait-for-human vs. auto-bypass, and chose auto-bypass).
  - Caps restarts at 3/day, then stops and sends one alert for manual
    attention instead of retrying blindly.
  - Skips restart (and alerts instead) if `.paytm_token.json` isn't fresh
    for today — restarting would just fail immediately. Token refresh
    (`python auth.py`) is an interactive browser login and is intentionally
    left to the human owner; this script never touches it.
  - After market close (15:35 IST), runs the bot's own `daily_summary.py`
    once and pushes it to WhatsApp via `notify.sh`.
  - Touch `PAUSE_AUTORESTART` in this directory to disable auto-restart
    without editing anything (daily summary still runs).
  - Never edits `trading_bot/config.yaml` or trading-mode settings.

- **`weekly_tuning.sh`** — via launchd (`com.vremployee.trading-weekly-tuning`),
  Sundays 18:00 IST: runs a local headless `claude -p` session (same
  pattern as the WhatsApp bridge) that analyzes the week's closed trades
  in `trades.db` against `config.yaml`, and writes a dated proposal to
  `tuning_proposals/YYYY-MM-DD.md` — **never edits config.yaml directly**.
  Review proposals yourself and apply changes by hand.

## State & logs

- `state.json` — today's restart count / dedup flags for supervisor.py.
  Resets automatically each new trading day.
- `~/Library/Logs/trading-supervisor.log`, `~/Library/Logs/trading-weekly-tuning.log`
  — launchd stdout/stderr.
- `weekly_tuning.log` — headless-claude run log for the tuning job.

## Known setup requirement: macOS Full Disk Access

Both launchd jobs need to read/write files under `~/Desktop`, which macOS's
TCC privacy protection blocks by default for background (non-interactive)
processes — even though running the same commands from Terminal works
fine. Until granted, both jobs silently no-op with an `Operation not
permitted` error in their log (no risk, just inactive).

One-time fix: **System Settings → Privacy & Security → Full Disk Access**,
add and enable:
- `/usr/bin/python3`
- `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`
- `/Users/bhanuja/.local/bin/claude`

(Use Cmd+Shift+G in the file picker to type each path directly.) Jobs pick
this up on their next scheduled tick — no restart needed, though you can
force one with `launchctl kickstart -k gui/$(id -u)/com.vremployee.trading-supervisor`.

## Disabling

```
launchctl unload ~/Library/LaunchAgents/com.vremployee.trading-supervisor.plist
launchctl unload ~/Library/LaunchAgents/com.vremployee.trading-weekly-tuning.plist
```
