# Kids Video Studio

A separate content line from the Mastery Path programming-tutorial channel
(`video-studio/`). This one produces **animated short stories for young
children**, bilingual in **English and Telugu**, built to run cleanly under
YouTube's rules for content directed at kids (COPPA / "Made for Kids",
YouTube Kids content policy, advertiser-friendly guidelines).

## The virtual employee

[`kids-animation-writer`](../.claude/agents/kids-animation-writer.md) is the
subagent that does this work. Ask for it directly in chat, e.g.:

> "Give me a kids-animation-writer script about a lion cub learning to
> share, English and Telugu, ~90 seconds."

It reads two reference docs before writing anything:

- [`SCRIPT_SCHEMA.md`](SCRIPT_SCHEMA.md) — the bilingual story/scene/dialogue
  format every script must follow.
- [`COMPLIANCE_CHECKLIST.md`](COMPLIANCE_CHECKLIST.md) — the YouTube kids
  regulatory checklist it runs every script through before marking it ready.

## Output layout

```
kids-video-studio/
  content/
    scripts/        bilingual story scripts (JSON, per SCRIPT_SCHEMA.md)
  render/            character SVGs, per-scene HTML/CSS animation, Playwright recorder
  voice/             per-scene multi-voice edge-tts narration (free, offline)
  assemble/          mux narration into each clip + concatenate into the final mp4
  output/renders/    finished bilingual .mp4 files
  build_video.py     orchestrates the above end-to-end
  README.md
  SCRIPT_SCHEMA.md
  COMPLIANCE_CHECKLIST.md
```

## Rendering a script to video

Animation and voice synthesis *are* wired up, entirely with free/offline
tools already vendored in this repo (no paid APIs, no network calls at
render time):

- **Characters & scenes** are hand-built flat-vector SVGs
  (`render/characters.py`) animated with CSS keyframes, staged per scene in
  `render/scene_poses.py`.
- **Narration** uses `edge-tts` (free Microsoft neural TTS) with a distinct
  voice per character per language, so kids can tell who's talking
  (`voice/narrate_scene.py`).
- **Recording** uses headless Chromium via Playwright to capture each
  scene's animation, timed exactly to that scene's narration
  (`render/record_scenes.py`) — same technique as the coding-tutorial
  pipeline in `video-studio/`.
- **Assembly** muxes audio into each clip and concatenates into the final
  h264/aac mp4 (`assemble/assemble.py`).

Run it (uses `video-studio/.venv`, which already has edge-tts + Playwright):

```bash
video-studio/.venv/bin/python kids-video-studio/build_video.py \
  kids-video-studio/content/scripts/<id>.json en te
```

Output lands in `output/renders/<id>-<lang>.mp4`. This is a simple, original
"limited animation" style (flat vector characters, CSS motion) — not
frame-by-frame character animation — chosen because it's fully scriptable
from free/open tooling already in this repo, with no external art or paid
generation services involved.

A `kids-video-preview` entry in [`.claude/launch.json`](../.claude/launch.json)
serves `_preview/*.html` on `localhost:8931` for eyeballing a single scene's
art/animation/captions in the browser before a full render.

## Guardrails that apply here

Per [CLAUDE.md](../CLAUDE.md) section 3: uploading or publishing a finished
video is an externally-visible action and always needs explicit go-ahead in
chat before it happens — scripting and compliance review do not.
