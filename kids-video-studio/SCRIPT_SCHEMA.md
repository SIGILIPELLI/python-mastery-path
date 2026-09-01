# Bilingual Kids Short — Script Schema

Every script `kids-animation-writer` produces is one JSON file with this
shape. Both language tracks are full, standalone versions of the same
story — not a translation bolted on as an afterthought.

```jsonc
{
  "id": "lion-cub-shares-honey",
  "format": "kids-short",
  "target_age_range": "3-7",
  "duration_seconds_target": 90,

  "moral_or_theme": "Sharing makes play more fun for everyone.",

  "characters": [
    {
      "id": "cub",
      "name_en": "Simba... (never an existing IP name — invent one)",
      "name_te": "<Telugu name>",
      "visual_description": "small orange lion cub, round ears, blue collar",
      "personality": "curious, a little impatient"
    }
  ],

  "voices": {
    "en": "en-US-AnaNeural",
    "te": "te-IN-ShrutiNeural"
  },

  "scenes": [
    {
      "scene_number": 1,
      "setting": "sunny savanna clearing, one big tree",
      "action": "Cub finds a pot of honey and hides it behind the tree.",
      "dialogue": [
        {
          "character": "cub",
          "line_en": "Mine, mine, all mine!",
          "line_te": "<Telugu line — natural, age-appropriate translation>"
        }
      ],
      "on_screen_text_en": null,
      "on_screen_text_te": null,
      "sound_music_notes": "light playful marimba, bird chirps"
    }
  ],

  "compliance": {
    "checklist_file": "kids-video-studio/COMPLIANCE_CHECKLIST.md",
    "status": "pass",
    "notes": "Any item that couldn't be fully satisfied, and why."
  },

  "metadata": {
    "title_en": "",
    "title_te": "",
    "description_en": "",
    "description_te": "",
    "tags": ["kids", "animated story", "..."],
    "thumbnail_concept": "one clear scene, big expressive character face, no text clutter",
    "made_for_kids": true
  }
}
```

## Writing rules

- **Voices** — default to `en-US-AnaNeural` (English, "Cartoon/Cute" style)
  and `te-IN-ShrutiNeural` (Telugu) unless the user asks for a specific
  preset. `te-IN-MohanNeural` is the Telugu male alternative. Verify current
  options with `video-studio/.venv/bin/edge-tts --list-voices` if this list
  ever goes stale.
- **Pacing** — spoken narration/dialogue should land within ~10% of
  `duration_seconds_target` at a slow, kid-friendly speaking rate
  (~2 words/second, slower than the adult-tutorial Shorts pipeline).
- **Scenes** — short and visual: one clear action per scene, simple enough
  to storyboard/animate directly from the `action` line. 6-12 scenes is
  typical for a 60-120s short.
- **Dialogue** — every line needs both `line_en` and `line_te`. Never leave
  one blank "for later."
- **On-screen text** — used sparingly (title cards, sound-effect words like
  "POP!"); provide both language variants whenever it's used, since text
  doesn't get dubbed.
- **No placeholder content** — don't write "[add joke here]" or invent a
  character/prop and leave its description empty. If a detail is genuinely
  undecided, ask the user rather than guessing.
- Run every finished script against
  [`COMPLIANCE_CHECKLIST.md`](COMPLIANCE_CHECKLIST.md) and fill in the
  `compliance` block honestly before calling it done.
