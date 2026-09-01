#!/bin/bash
# Weekly trading-bot config-tuning analysis, run headless via launchd.
# Read-only analysis + one new proposal file — never touches config.yaml,
# credentials, or the live bot process. See tuning_prompt.md for the task.
set -uo pipefail
cd /Users/bhanuja/Desktop/vremployee || exit 1

PROMPT="$(cat /Users/bhanuja/Desktop/vremployee/trading-ops/tuning_prompt.md)"
LOG=/Users/bhanuja/Desktop/vremployee/trading-ops/weekly_tuning.log

echo "=== $(date) ===" >> "$LOG"
/Users/bhanuja/.local/bin/claude -p "$PROMPT" --permission-mode acceptEdits --output-format json >> "$LOG" 2>&1
