# Video script JSON schema

Both `yt-shorts-writer` and `yt-longform-producer` write one JSON file per
video to `video-studio/output/scripts/<slug>.json`. The render pipeline
(`make_video.py`) only understands this shape — nothing else.

```jsonc
{
  "type": "short",                 // "short" | "longform"
  "language": "python",            // matches catalog.json "language"
  "title": "Why your Python loop needs an `else` (nobody uses this)", // MUST be <=100 chars -- YouTube rejects the upload with "invalid title" otherwise (hit for real on 2026-08-27, a 109-char long-form title)
  "description": "Full YouTube description text. Must end with a\n\nSource lesson(s):\n- <url>\n- <url>",
  "tags": ["python", "for loops", "programming tutorial"],
  "voice": "en-US-JennyNeural",     // female neural voice, warm/natural
  "source_urls": ["https://sigilipelli.github.io/python-mastery-path/level-1/03-control-flow/"],
  "beats": [
    {
      "narration": "What one or two sentences the voice speaks during this beat. Written to be SAID ALOUD -- contractions, short clauses, no markdown.",
      "display": {
        "kind": "title_card",      // "title_card" | "editor" | "terminal" | "text" | "stick"
        "heading": "Control Flow",
        "subheading": "Python Mastery Path -- Level 1"
      }
    },
    {
      "narration": "...",
      "display": {
        "kind": "editor",          // types this code into a code-editor mock, no output shown
        "lang": "python",
        "code": "score = 82\n\nif score >= 90:\n    grade = \"A\"\n..."
      }
    },
    {
      "narration": "...",
      "display": {
        "kind": "terminal",        // types code, then reveals a terminal output block below it
        "lang": "python",
        "code": "print(describe(0))",
        "output": "zero"
      }
    },
    {
      "narration": "...",
      "display": {
        "kind": "stick",            // animated stick-figure scene (see below)
        "scene": "balance",
        "heading": "Tradeoffs",
        "subheading": "speed vs scope"   // optional; keep it 2-4 words
      }
    },
    {
      "narration": "Closing line + call to action to read the full lesson.",
      "display": {
        "kind": "text",
        "heading": "Full lesson + runnable code:",
        "subheading": "sigilipelli.github.io/python-mastery-path/level-1/03-control-flow/"
      }
    }
  ]
}
```

## `stick` beats -- animated stick figures (REQUIRED in every script)

`kind: "stick"` renders a lively, always-moving stick-figure scene behind the
synced narration caption. Fields: `scene` (one of the names below), `heading`
(a 1-3 word on-screen label), optional `subheading` (2-4 words -- omit if it
would just echo the narration). No `code`/`lang`/`output`.

**Every script MUST use `stick` beats** -- they are the channel's main
engagement lever. Minimums:
- **Short**: at least 2 -- the cold-open hook beat and the payoff beat.
  A 3rd on a middle beat is good if a scene genuinely fits.
- **Long-form**: the opening framing beat, the closing recap/CTA beat, and
  at least one scene inside roughly every other section -- never a section
  with zero motion.

**Relevance is mandatory.** Pick the scene that literally depicts what the
narration says on that beat. If nothing fits, use `wave` (intro), `point`
(a key claim), `celebrate` (payoff), or `think` (a question) -- never force
an unrelated scene. Code-only concepts that a scene can't honestly show
should stay `editor`/`terminal` beats.

Scene catalog:

| scene | shows | use it when the narration is about |
|---|---|---|
| `wave` | figure waving | opening / greeting / "in this video" |
| `think` | figure tapping chin, "?" | posing a question, a puzzle, "why does this happen" |
| `point` | figure jabbing forward, "!" | a key rule, a warning, the one thing to remember |
| `celebrate` | arms up, hopping | the payoff, it works, you're done |
| `confused` | shrugging, "?" | a gotcha, a surprising result, "this looks wrong" |
| `idea` | lightbulb pops on | a new concept / framework / better approach |
| `search` | sweeping a magnifier | discovery, research, digging into the real cause |
| `write` | scribbling on a doc | writing requirements, a PRD, docs, notes |
| `present` | gesturing at a bar chart | showing data / results / a demo |
| `measure` | same, green accent | metrics, KPIs, a North Star, tracking a number |
| `balance` | figure holding a tilting scale (A vs B) | a tradeoff, weighing two options, pros/cons |
| `prioritize` | pointing at the top of a 1-2-3 stack | ranking, RICE, "what do we build first" |
| `roadmap` | walking past NOW / NEXT / LATER posts | roadmapping, planning horizons, sequencing |
| `checklist` | ticking a 3-row checklist | acceptance criteria, a review checklist, non-goals |
| `climb` | climbing steps, up-arrow | growth, leveling up, career progression, progress |
| `discuss` | two figures talking, bubbles | collaboration, stakeholder communication, alignment |
| `pushback` | one figure shoving, other recoils, "!" | disagreement, pushback, conflict, saying no |
| `handshake` | two figures shake hands | agreement, buy-in, a deal, alignment reached |
| `handoff` | one returns a box, other receives | a function returning, delegation, passing work on |
| `sequential` | one worker runs, others wait ("zzz") | single-threaded / blocking / one-at-a-time execution |
| `parallel` | 4 workers all busy | multi-core, parallelism, concurrent work |
| `blocked` | figures stuck on spinners | waiting on I/O, blocked threads, a bottleneck |
| `gil` | one holds the lock, others blocked | a global lock / mutex / the Python GIL |

Advanced: `scene: "custom"` with a `figures` array
(`[{"anim": "...", "label": "...", "prop": "...", "extra_class": "accent|warn"}]`)
composes an arbitrary row -- only reach for this if no named scene fits.

## Rules for writing `narration`

- Written to be spoken, not read: short sentences, contractions ("it's",
  "you'll"), natural rhythm. No bullet points, no markdown, no code syntax
  read literally character-by-character -- describe what the code *does*.
- Warm and encouraging tone, like a patient senior engineer explaining
  something to a friend. Never condescending, never hype-bro, no filler
  ("alright guys", "let's dive in").
- One beat = roughly 6-14 seconds of speech (~15-40 words). The renderer
  times each beat's on-screen animation to the narration's actual audio
  duration, so don't pad or rush.

## Timing budgets

Measured speaking rate for the default voice/rate settings is **~2.5
words/second** (not a rough guess -- measured from real rendered output).
Use that to budget word counts before writing:

- `short`: total narration should land 35-55 seconds -> **90-140 words**
  total. Typically 4-7 beats: a `stick` hook, 1-2 code (or `text`/`stick`)
  beats, a `stick` payoff, CTA.
- `longform`: total narration should land 8-11 minutes (480-660s) ->
  **1200-1650 words** total. Undershooting this is the most common mistake --
  a 3-lesson video needs real depth per lesson (5-8 beats each: intro,
  3-5 code beats covering more than just the single most obvious example,
  recap), not just one code beat per lesson. When in doubt, cover one more
  genuinely relevant sub-topic from the same lesson rather than padding
  narration with filler. Close with one `text` beat listing every source
  URL used.

After writing, sum `len(narration.split())` across all beats and sanity
check it lands in the target range before finalizing.

## Source links are mandatory

Every script's `source_urls` must list the exact `url` field(s) pulled from
`video-studio/content/catalog.json` for every lesson referenced -- never
invent or guess a URL. The final `text`/outro beat and the YouTube
`description` must both surface these links.
