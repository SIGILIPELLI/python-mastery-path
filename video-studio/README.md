# Video Studio — the YouTube content creator employee

Turns the Mastery Path lesson content (this repo + the sibling
`*-mastery-path` repos on the Desktop) into narrated tutorial videos, with a
warm, human (not robotic) female voice, and every video linking back to its
source lesson page.

## How it works

```
catalog.json  →  script JSON (written by a subagent)  →  make_video.py  →  final .mp4 + metadata.txt
```

1. **Content ingestion** (`content/build_catalog.py`) scans every local
   `*-mastery-path` repo's `docs/*.md`, and writes `content/catalog.json`: one
   entry per lesson with its title, sections, code blocks, and live URL.
   Re-run this after any lesson content changes:
   ```bash
   .venv/bin/python content/build_catalog.py
   ```

2. **Two writer subagents** (`.claude/agents/`) read the catalog and write a
   script JSON to `output/scripts/` — they never touch audio/video directly.
   Invoke them from a normal Claude Code chat:
   - **`yt-shorts-writer`** — one lesson → one 35-55s YouTube Short.
     > "Use yt-shorts-writer to make a short about Python's walrus operator"
   - **`yt-longform-producer`** — several related lessons → one ~10 minute
     video.
     > "Use yt-longform-producer to cover Level 1 fundamentals in one video"

   The exact JSON shape both agents follow is documented in
   `content/SCRIPT_SCHEMA.md`.

3. **Render pipeline** (`make_video.py`) takes a script JSON and produces the
   finished video:
   ```bash
   .venv/bin/python make_video.py --script output/scripts/<name>.json
   ```
   Internally:
   - `voice/narrate.py` — synthesizes narration per beat with `edge-tts`
     (free, neural, non-robotic voice — default `en-US-JennyNeural`, warm
     and polite). Real durations are measured from the generated audio.
   - `render/record.py` + `render/beat_template.py` — renders each beat as a
     simulated code-typing / terminal-output animation (no human screen
     capture needed) in a headless browser, timed to match that beat's
     narration exactly. Includes karaoke-style burned-in captions.
   - `assemble/assemble.py` — muxes narration into each clip, transcodes to
     h264/aac, and concatenates into the final MP4.

   Output: `output/renders/<name>.mp4` and a companion
   `<name>.metadata.txt` with the title, description, tags, and source
   lesson links — for you to review before uploading. **Nothing is ever
   auto-published** — uploading to YouTube is always a manual step you do
   yourself.

4. **Upload** (`upload/upload_cli.py`) pushes a rendered video to YouTube via
   the Data API, pulling title/description/tags straight from its script
   JSON:
   ```bash
   .venv/bin/python upload/upload_cli.py --script output/scripts/<name>.json
   ```
   Defaults to `--privacy private` — never public unless explicitly told
   (`--privacy unlisted` or `--privacy public`). This is never run on a
   schedule; it's only ever invoked after a human go-ahead in chat, per the
   "confirm before publishing" rule. First run opens a browser for a
   one-time OAuth consent (you log in as the channel's Google account and
   click Allow — that step has to be yours, not automated); after that a
   cached token (`credentials/token.json`, gitignored) is reused silently.

## Google Cloud / YouTube API setup

Already done for this channel (vsigilipelli@gmail.com):
- Google Cloud project `mastery-path-youtube`, YouTube Data API v3 enabled.
- OAuth consent screen: External audience, **Testing** publishing status
  (avoids Google's app-verification process since it's just for this one
  channel), with vsigilipelli@gmail.com added as a test user.
- OAuth client `Video Studio Uploader` (Desktop app type) →
  `credentials/client_secret.json` (gitignored, never commit).

**Quota constraint:** the default free quota is 10,000 units/day and each
upload costs 1,600 units — a hard ceiling of **~6 uploads/day**, not more,
until/unless a quota increase is requested from Google (not guaranteed,
days-to-weeks turnaround). Plan daily batches accordingly (e.g. 5 Shorts +
1 long-form).

## One-time setup

Already done in this environment:
```bash
brew install ffmpeg
python3 -m venv .venv
.venv/bin/pip install edge-tts playwright google-auth-oauthlib google-api-python-client
.venv/bin/playwright install chromium
```

## Notes

- `edge-tts` is a free wrapper around Microsoft Edge's neural voices (same
  engine as Azure Neural TTS) — no API key needed. It's an unofficial/
  reverse-engineered client, not a licensed commercial API, but is very
  widely used for exactly this kind of narration.
- Shorts render vertical (1080x1920); long-form renders horizontal
  (1920x1080) — set automatically from the script's `"type"`.
- Never invents code or links: both subagents are instructed to pull
  everything verbatim from `catalog.json`, tracing back to a real lesson.
