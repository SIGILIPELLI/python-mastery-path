#!/usr/bin/env python3
"""
Trading-bot ops supervisor.

Runs on a short interval (every ~2 min via launchd, see
com.vremployee.trading-supervisor.plist). Each invocation is a single
stateless-ish tick that:

  1. Checks whether trading_bot's `main.py --mode live` process is up.
  2. If it's down during market hours and the shutdown wasn't a manual
     Ctrl-C/SIGTERM (checked via the day's log file), treats it as a crash:
     auto-restarts it (piping the bot's own "YES I UNDERSTAND" live-mode
     confirmation), up to MAX_RESTARTS_PER_DAY times, then gives up and
     alerts for manual attention.
  3. Skips restart (and alerts instead) if the Paytm access token isn't
     fresh for today — restarting would just fail again immediately.
  4. After market close, runs daily_summary.py once and pushes it to
     WhatsApp.

State (restart counts, dedup flags, etc.) is kept in state.json next to
this script, reset each new trading day. Touch PAUSE_AUTORESTART in this
directory to disable auto-restart without editing anything (daily summary
still runs).

This script never modifies trading_bot/config.yaml and never touches the
Paytm OAuth login itself (auth.py requires an interactive browser login
and is left entirely to the human owner).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

OPS_DIR = Path(__file__).parent
BOT_DIR = Path("/Users/bhanuja/Desktop/my_claude_project/trading_bot")
NOTIFY_SH = Path("/Users/bhanuja/Desktop/vremployee/whatsapp-bridge/notify.sh")
STATE_PATH = OPS_DIR / "state.json"
PAUSE_FLAG = OPS_DIR / "PAUSE_AUTORESTART"

VENV_PYTHON = BOT_DIR / ".venv" / "bin" / "python3"
MAX_RESTARTS_PER_DAY = 3
DAILY_REPORT_AFTER_HOUR = 15
DAILY_REPORT_AFTER_MINUTE = 35
MARKET_OPEN_CHECK_FROM = (9, 10)   # start looking for the process a little before 09:15
MARKET_CHECK_UNTIL = (15, 30)


def now_ist() -> datetime:
    return datetime.now(IST)


def today_str() -> str:
    return now_ist().date().isoformat()


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def fresh_state_for_today() -> dict:
    return {
        "date": today_str(),
        "restart_count": 0,
        "manual_stop_today": False,
        "giveup_alert_sent": False,
        "token_alert_sent": False,
        "daily_report_sent": False,
    }


def notify(message: str) -> None:
    try:
        subprocess.run(
            [str(NOTIFY_SH), message],
            capture_output=True,
            timeout=20,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        print(f"[supervisor] notify.sh failed ({e}); message was: {message}", file=sys.stderr)


def is_bot_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-f", "main.py --mode live"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def is_trading_window() -> bool:
    """Loose window where we expect the bot to be up: ~09:10-15:30 IST, weekday."""
    n = now_ist()
    if n.weekday() >= 5:
        return False
    holidays_path = BOT_DIR / "config" / "holidays.json"
    try:
        holidays = set(json.loads(holidays_path.read_text()).get("holidays", []))
        if n.date().isoformat() in holidays:
            return False
    except OSError:
        pass
    start = n.replace(hour=MARKET_OPEN_CHECK_FROM[0], minute=MARKET_OPEN_CHECK_FROM[1], second=0, microsecond=0)
    end = n.replace(hour=MARKET_CHECK_UNTIL[0], minute=MARKET_CHECK_UNTIL[1], second=0, microsecond=0)
    return start <= n <= end


def is_after_report_time() -> bool:
    n = now_ist()
    if n.weekday() >= 5:
        return False
    return (n.hour, n.minute) >= (DAILY_REPORT_AFTER_HOUR, DAILY_REPORT_AFTER_MINUTE)


def last_shutdown_was_manual() -> bool:
    """
    Inspect today's bot log for a clean SIGINT/SIGTERM shutdown as the last
    thing that happened (main.py's _handle_sigint logs this before "Bot
    stopped."). If the log instead just stops mid-tick, or ends on an
    exception, treat it as a crash.
    """
    log_path = BOT_DIR / "logs" / f"bot_{today_str()}.log"
    if not log_path.exists():
        return False
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return False
    tail = lines[-15:]
    tail_text = "\n".join(tail)
    return "Interrupt received" in tail_text and "Bot stopped." in tail_text


def last_log_line() -> str:
    log_path = BOT_DIR / "logs" / f"bot_{today_str()}.log"
    if not log_path.exists():
        return "(no log file for today)"
    try:
        lines = log_path.read_text(errors="replace").splitlines()
        return lines[-1] if lines else "(empty log)"
    except OSError:
        return "(could not read log)"


def token_is_fresh() -> bool:
    token_path = BOT_DIR / ".paytm_token.json"
    if not token_path.exists():
        return False
    try:
        data = json.loads(token_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    saved_at = data.get("saved_at", "")
    return saved_at.startswith(today_str())


def attempt_restart() -> None:
    log_file = BOT_DIR / "logs" / "live_restart_stdout.log"
    with log_file.open("a") as out:
        proc = subprocess.Popen(
            [str(VENV_PYTHON), "main.py", "--mode", "live"],
            cwd=str(BOT_DIR),
            stdin=subprocess.PIPE,
            stdout=out,
            stderr=out,
            start_new_session=True,
            text=True,
        )
    try:
        proc.stdin.write("YES I UNDERSTAND\n")
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass


def run_daily_report() -> None:
    result = subprocess.run(
        [str(VENV_PYTHON), "daily_summary.py"],
        cwd=str(BOT_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )
    summary = result.stdout.strip() or result.stderr.strip() or "(no output)"
    notify(f"📊 Trading bot — daily summary ({today_str()}):\n\n{summary}")


def main() -> None:
    state = load_state()
    if state.get("date") != today_str():
        state = fresh_state_for_today()

    running = is_bot_running()

    if running:
        state["manual_stop_today"] = False
    elif is_trading_window():
        if not state.get("manual_stop_today") and not state.get("giveup_alert_sent"):
            if last_shutdown_was_manual():
                state["manual_stop_today"] = True
                print("[supervisor] bot down: manual stop detected, not restarting.")
            elif PAUSE_FLAG.exists():
                print("[supervisor] bot down (crash-looking) but PAUSE_AUTORESTART is set — skipping.")
            elif state.get("restart_count", 0) >= MAX_RESTARTS_PER_DAY:
                if not state.get("giveup_alert_sent"):
                    notify(
                        f"🛑 Trading bot has crashed and hit the daily auto-restart "
                        f"limit ({MAX_RESTARTS_PER_DAY}). Last log line: "
                        f"{last_log_line()}\nNot retrying further today — needs "
                        f"manual attention."
                    )
                    state["giveup_alert_sent"] = True
            elif not token_is_fresh():
                if not state.get("token_alert_sent"):
                    notify(
                        "⚠️ Trading bot is down and the Paytm access token isn't "
                        "fresh for today. Run `python auth.py` in trading_bot to "
                        "re-authenticate, then it can restart."
                    )
                    state["token_alert_sent"] = True
            else:
                reason = last_log_line()
                attempt_restart()
                state["restart_count"] = state.get("restart_count", 0) + 1
                notify(
                    f"⚠️ Trading bot crashed (last log line: {reason}). "
                    f"Auto-restarted — attempt {state['restart_count']}/"
                    f"{MAX_RESTARTS_PER_DAY}."
                )

    if is_after_report_time() and not state.get("daily_report_sent"):
        run_daily_report()
        state["daily_report_sent"] = True

    save_state(state)


if __name__ == "__main__":
    main()
