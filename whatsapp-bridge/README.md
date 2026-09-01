# WhatsApp Bridge

Two-way WhatsApp channel for the [virtual employee](../CLAUDE.md): status updates go
out to the owner's WhatsApp, and messages the owner sends in their **"Message
yourself"** self-chat come back in as commands, run through Claude Code headless in
the workspace, with the answer replied in WhatsApp.

Built on [whatsapp-web.js](https://wwebjs.dev/) (unofficial WhatsApp Web automation —
linked like a normal "WhatsApp Web" device via QR; no API accounts). The Mac must be
on and the bridge running for the channel to work.

## First-time setup

```bash
cd whatsapp-bridge
npm install          # already done
node index.js        # prints + saves a QR code to qr.png
```

Scan the QR with your phone: **WhatsApp → Settings → Linked Devices → Link a
Device**. The session is stored in `.wwebjs_auth/` (gitignored) so you only scan
once.

## Using it from your phone

Open WhatsApp and message **yourself** (the "You" chat). The bridge replies with a 🤖
prefix (and ignores its own 🤖 messages, so there are no loops).

- `status` / `tasks` — live summary of [TASKS.md](../TASKS.md)
- `ping` — is the bridge alive?
- `new` — start a fresh Claude conversation (drops remembered context)
- `help` — this list
- **anything else** — sent to `claude -p` in the workspace root; the reply comes
  back to WhatsApp. Conversation context carries across messages (via `--resume`)
  until you say `new`. Long tasks can take minutes; you get a "Working on it" ack.

Headless runs use `--permission-mode acceptEdits` (see `config.json`) and are
instructed to **stop at the operating charter's confirmation guardrails** — anything
destructive/external/financial/production gets described, not done, and must be
approved from a real Claude Code session on the Mac.

## Sending status updates from other sessions / scheduled tasks

```bash
/Users/bhanuja/Desktop/vremployee/whatsapp-bridge/notify.sh "Task #35 done: …"
```

POSTs to the bridge's local endpoint (`127.0.0.1:8787/send`, plain-text body).
`GET /health` returns 200 when the WhatsApp link is ready. `POST /test-inbound`
sends an *unprefixed* message to the self-chat — it loops back through real
WhatsApp and exercises the inbound command path (debug use). All loopback-only.

Note: self-chat addressing mixes id formats per sending device — phone-sent
texts arrive `@c.us → @lid`, bridge-sent ones `@lid → @lid`. On ready the bridge
resolves BOTH of the account's ids (`getMaybeMePnUser`/`getMaybeMeLidUser`) and
the inbound filter accepts `fromMe` messages addressed to either; never compare
against `client.info.wid` alone.

24/7: the launchd job wraps node in `caffeinate -si`, which blocks idle/system
sleep while the bridge runs (no sudo, ends with the process). A MacBook with the
lid closed on battery still sleeps — keep it on power or lid-open.

## Keeping it running (auto-start)

**Installed 2026-07-20**: the launchd agent (`~/Library/LaunchAgents/com.vremployee.whatsapp-bridge.plist`)
starts the bridge at login and restarts it on crash. Logs go to
`~/Library/Logs/whatsapp-bridge.log`.

- Restart: `launchctl kickstart -k gui/$(id -u)/com.vremployee.whatsapp-bridge`
- Stop/remove: `launchctl bootout gui/$(id -u)/com.vremployee.whatsapp-bridge`

launchd quirks discovered while setting this up (both handled):

1. The plist must NOT use a `WorkingDirectory`/log path under `~/Desktop` — TCC
   makes the spawn fail with `EX_CONFIG` (status 78) before node even starts.
2. Under launchd, whatsapp-web.js's post-auth flow silently stalls before emitting
   `ready` (page is CONNECTED, evaluations work). `index.js` has a watchdog that
   detects "authenticated but not ready after 60s" and replays the library's own
   inject → client-info → attach-listeners → ready sequence manually.

`index.js` also handles SIGTERM/SIGINT with a clean `client.destroy()` — without
it, node swallows TERM and leaves a zombie holding port 8787 and the Chromium
profile.

## Notes & caveats

- whatsapp-web.js is unofficial; WhatsApp could in principle flag accounts using
  automated clients. Chosen knowingly (2026-07-20) over the official Meta/Twilio
  APIs to avoid account/webhook setup.
- If WhatsApp logs the device out, delete `.wwebjs_auth/` and re-run to get a new QR.
- `config.json`: `port`, `claudePath`, `claudeArgs` (permission mode), `timeoutMinutes`.
