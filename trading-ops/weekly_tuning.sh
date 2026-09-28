#!/bin/bash
# Weekly trading-bot config-tuning analysis, run headless via launchd.
# Read-only analysis + one new proposal file — never touches config.yaml,
# credentials, or the live bot process. See tuning_prompt.md for the task.
set -uo pipefail
umask 077  # proposals and logs contain trading data: owner-only

OPS_DIR="$(cd "$(dirname "$0")" && pwd)"
export TRADING_BOT_DIR="${TRADING_BOT_DIR:-$HOME/Desktop/my_claude_project/trading_bot}"
export OPS_DIR
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
cd "$OPS_DIR/.." || exit 1

# tuning_prompt.md uses $TRADING_BOT_DIR / $OPS_DIR placeholders so no
# absolute paths live in the repo.
PROMPT="$(envsubst '$TRADING_BOT_DIR $OPS_DIR' < "$OPS_DIR/tuning_prompt.md")"
LOG="$OPS_DIR/weekly_tuning.log"

echo "=== $(date) ===" >> "$LOG"
"$CLAUDE_BIN" -p "$PROMPT" --permission-mode acceptEdits --output-format json >> "$LOG" 2>&1
