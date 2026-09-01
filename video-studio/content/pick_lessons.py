#!/usr/bin/env python3
"""
Sequential-subject rotation state manager for the daily video batch.

QUOTA MODEL (set 2026-08-27 per explicit user instruction): every subject's
target is exactly 30 Shorts + 6 long-forms -- one long-form for every batch
of 5 Shorts (30 / 5 = 6, so every daily batch produces both, until the
6-longform cap is hit). A subject is "complete" once it has produced 30
Shorts (repeats count -- see below) AND 6 long-forms, not merely "every
lesson touched once" (the old rule, which let thin subjects like
product-manager -- 10 real lessons -- finish after just 11 videos total,
which is what prompted this rework: playlists were real but shallow because
most subjects don't have anywhere near 30 lessons of source content yet).

Most subjects don't yet have 30 distinct real (non-stub) lessons -- many
only have Level 1 written (see TASKS.md task #86's ongoing content
backfill, a separate effort from this video pipeline). Rather than block
video production on that, once a subject's real lessons have each been
shorted once, this script starts re-issuing the least-recently-used lessons
for additional Shorts. `short_repeat_counts` in the output tells the writer
agent how many times a slug has already been shorted, so it picks a
genuinely different angle each time -- never inventing content that isn't
in the lesson, just covering a different real section/example from it.

Long-forms are sourced in priority order, one per batch, until 6 are hit:
  1. One per available level (1-4) that doesn't have a longform yet. If that
     level has a real lesson with "project" or "capstone" in its slug, it's
     a dedicated single-lesson deep-dive (`kind: "level_capstone"`);
     otherwise a multi-lesson roundup of that level (`kind: "level_roundup"`).
  2. Once every available level has a longform, any remaining "project"/
     "capstone"-slug lesson that was folded into a roundup rather than given
     its own dedicated video gets promoted to a dedicated deep-dive
     (`kind: "project"`) -- still real, distinct lesson content, just a
     closer look than the roundup gave it.
  3. If still short of 6 (subjects with fewer than 4 written levels and no
     more project/capstone lessons to promote), the rest are thematic
     cross-lesson roundups (`kind: "theme"`) -- yt-longform-producer picks a
     coherent, not-yet-covered lesson cluster itself, same as (1)'s roundup
     style, just not tied to a single level.

Usage:
    .venv/bin/python content/pick_lessons.py
Prints JSON to stdout:
    {"language": ...,
     "short_slugs": [...5 slugs...],
     "short_repeat_counts": {slug: N, ...},   # N-1 = how many prior Shorts already used this slug
     "longform": null
               | {"kind": "level_roundup", "level": "level-3"}
               | {"kind": "level_capstone", "level": "level-4", "slug": "..."}
               | {"kind": "project", "slug": "..."}
               | {"kind": "theme"}}
`longform` is null only once a subject has already reached 6 long-forms but
still needs more Shorts (repeats) to reach 30.
Also advances and persists rotation_state.json so the next run picks up
where this one left off.
"""
import json
from pathlib import Path

STATE_PATH = Path(__file__).parent / "rotation_state.json"
CATALOG_PATH = Path(__file__).parent / "catalog.json"

# Fixed subject order for the sequential (complete-one-then-move-on) scheme.
# Set 2026-08-10 per explicit user instruction: python first, then
# product-manager, then c, then the rest of the original 12-language
# round-robin order, then the remaining leadership/testing/cloud/ai/embedded/
# language categories.
SUBJECT_ORDER = [
    "python", "product-manager", "c",
    "java", "javascript", "shell", "cpp", "go", "sql", "rust", "typescript", "ruby", "php",
    "product-lead", "project-manager", "ai-manager", "servant-leadership",
    "java-testing", "cpp-testing", "python-testing",
    "aws", "azure", "gcp", "ibm-cloud", "adobe",
    "ai-ml", "llm-dev", "rag",
    "embedded", "embedded-linux", "embedded-python", "freertos", "edge-ai", "s32k",
    "dart", "kotlin", "powershell", "r", "scala", "swift",
]
LEVELS = ["level-1", "level-2", "level-3", "level-4"]
SHORTS_TARGET = 30
LONGFORM_TARGET = 6
BATCH_SIZE = 5


def load_state() -> dict:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
    else:
        state = {}
    state.setdefault("mode", "sequential")
    state.setdefault("current_subject_index", 0)
    # short_uses[subject][slug] = number of times that slug has been shorted
    state.setdefault("short_uses", {})
    # longform_used[subject] = [{"kind": ..., "level": ..., "slug": ...}, ...]
    state.setdefault("longform_used", {})
    state.setdefault("completed_subjects", [])
    return state


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def usable_candidates(catalog: list[dict], subject: str) -> list[str]:
    """Lessons with real written content -- excludes overview pages and stubs."""
    return [
        e["slug"] for e in catalog
        if e["language"] == subject and not e["is_overview"] and e.get("sections")
    ]


def available_levels(catalog: list[dict], subject: str) -> list[str]:
    """Levels that currently have at least one real (non-stub) lesson."""
    levels = set()
    for e in catalog:
        if (e["language"] == subject and not e["is_overview"]
                and e.get("sections") and e.get("level")):
            levels.add(e["level"])
    return [lvl for lvl in LEVELS if lvl in levels]


def project_slug_for_level(catalog: list[dict], subject: str, level: str) -> str | None:
    """Slug of the level's project/capstone lesson, if it has real content."""
    for e in catalog:
        if (e["language"] == subject and e.get("level") == level
                and not e["is_overview"] and e.get("sections")
                and ("capstone" in e["slug"] or "project" in e["slug"])):
            return e["slug"]
    return None


def all_project_slugs(catalog: list[dict], subject: str) -> list[str]:
    """Every project/capstone-tagged real lesson across all levels, in level order."""
    out = []
    for lvl in LEVELS:
        s = project_slug_for_level(catalog, subject, lvl)
        if s:
            out.append(s)
    return out


def pick_short_slugs(candidates: list[str], uses: dict, count: int = BATCH_SIZE) -> list[str]:
    """Pick `count` slugs, preferring never-used ones, then the least-used --
    so once a subject's real lessons are exhausted, repeats spread evenly
    across the whole subject instead of hammering one lesson."""
    if not candidates:
        return []
    ranked = sorted(candidates, key=lambda s: (uses.get(s, 0), candidates.index(s)))
    return ranked[:count]


def next_longform(catalog: list[dict], subject: str, levels: list[str], lf_used: list[dict]) -> dict:
    used_levels = {e["level"] for e in lf_used if e.get("kind") in ("level_roundup", "level_capstone")}
    used_slugs = {e["slug"] for e in lf_used if e.get("slug")}

    next_level = next((lvl for lvl in levels if lvl not in used_levels), None)
    if next_level:
        proj_slug = project_slug_for_level(catalog, subject, next_level)
        if proj_slug:
            return {"kind": "level_capstone", "level": next_level, "slug": proj_slug}
        return {"kind": "level_roundup", "level": next_level}

    remaining_project = next(
        (s for s in all_project_slugs(catalog, subject) if s not in used_slugs), None
    )
    if remaining_project:
        return {"kind": "project", "slug": remaining_project}

    return {"kind": "theme"}


def main():
    state = load_state()
    catalog = json.loads(CATALOG_PATH.read_text())

    idx = state["current_subject_index"] % len(SUBJECT_ORDER)
    tried = 0
    while SUBJECT_ORDER[idx] in state["completed_subjects"] and tried < len(SUBJECT_ORDER):
        idx = (idx + 1) % len(SUBJECT_ORDER)
        tried += 1
    subject = SUBJECT_ORDER[idx]

    candidates = usable_candidates(catalog, subject)
    uses = state["short_uses"].setdefault(subject, {})
    short_slugs = pick_short_slugs(candidates, uses)
    for s in short_slugs:
        uses[s] = uses.get(s, 0) + 1
    short_repeat_counts = {s: uses[s] for s in short_slugs}
    total_shorts_produced = sum(uses.values())

    levels = available_levels(catalog, subject)
    lf_used = state["longform_used"].setdefault(subject, [])
    longform = None
    if len(lf_used) < LONGFORM_TARGET:
        longform = next_longform(catalog, subject, levels, lf_used)
        lf_used.append(longform)

    subject_complete = total_shorts_produced >= SHORTS_TARGET and len(lf_used) >= LONGFORM_TARGET
    if subject_complete:
        if subject not in state["completed_subjects"]:
            state["completed_subjects"].append(subject)
        state["current_subject_index"] = (idx + 1) % len(SUBJECT_ORDER)
    else:
        state["current_subject_index"] = idx

    save_state(state)

    print(json.dumps({
        "language": subject,
        "short_slugs": short_slugs,
        "short_repeat_counts": short_repeat_counts,
        "longform": longform,
    }, indent=2))


if __name__ == "__main__":
    main()
