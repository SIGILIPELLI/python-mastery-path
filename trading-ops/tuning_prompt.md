Analyze /Users/bhanuja/Desktop/my_claude_project/trading_bot/logs/trades.db (positions and agent_decisions tables) for trades closed in the last 7 days, alongside the current /Users/bhanuja/Desktop/my_claude_project/trading_bot/config/config.yaml.

For each enabled agent under `agents:` in config.yaml, compute its win rate when it agreed with a trade's realized direction — same methodology as the existing dated comments already in that file (see the 2026-07-15/07-16/07-17 entries under `agents:` and `risk:` for the pattern and tone to match). Also check the exit-reason distribution (TP/SL/MAX_HOLD), overall win rate, and net P&L for the week.

Write a dated proposal file to /Users/bhanuja/Desktop/vremployee/trading-ops/tuning_proposals/<YYYY-MM-DD>.md containing:
- A data summary (trade count, win rate, exit-reason breakdown, per-agent agreement win rates, net P&L).
- Specific proposed config.yaml changes: parameter name, current value, proposed value, and rationale grounded in the data.
- Explicit sample-size / confidence caveats — flag when a week's data is too thin to act on.

Do NOT edit trading_bot/config.yaml itself — this is a proposal for human review only, never auto-applied. Do NOT touch .env, .paytm_token.json, or any Paytm credentials. Do NOT start, stop, or restart the live bot process — this task is read-only analysis plus writing one new file.

After writing the proposal file, push a short WhatsApp notification via:
  /Users/bhanuja/Desktop/vremployee/whatsapp-bridge/notify.sh "message"
saying a new tuning proposal is ready and its file path. If notify.sh exits non-zero, note that in your final output but don't treat it as a failure of the task.

Finally, add a row (or update the existing trading-ops row) in /Users/bhanuja/Desktop/vremployee/TASKS.md noting the new proposal, its date, and a one-line summary of the headline suggestion.

If trades.db has fewer than ~15 closed trades in the window, say so explicitly in the proposal file and keep suggestions minimal/tentative rather than over-fitting to noise.
