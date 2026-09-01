#!/usr/bin/env python3
"""Builds mobile-app/assets/content/manifest.json for the Quiz Academy app.

Sources:
  - video-studio/output/scripts/*.json -- the DURABLE record of every lesson
    video ever produced (title, description, source lesson URLs). This is the
    catalog backbone: `output/renders/` is pruned by the daily pipeline once a
    video is uploaded to YouTube, so it must never be the source of truth for
    which lessons exist.
  - video-studio/output/renders/*.mp4 -- whichever videos happen to be on local
    disk right now. Presence only sets a lesson's `videoAvailable` flag.
  - mobile-app/tool/questions.json -- authored MCQs keyed by lesson id (the
    script filename stem). Missing entries yield an empty list.
  - ~/Desktop/*-mastery-path -- every other Mastery Path track, listed as
    "coming_soon" until lessons exist for it.

Run after rendering new videos or updating questions.json:
    python3 mobile-app/tool/generate_manifest.py
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "video-studio" / "output" / "scripts"
RENDERS_DIR = REPO_ROOT / "video-studio" / "output" / "renders"
QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.json"
OUT_FILE = REPO_ROOT / "mobile-app" / "assets" / "content" / "manifest.json"
DESKTOP_DIR = Path.home() / "Desktop"

DISPLAY_NAMES = {
    "python": "Python", "java": "Java", "javascript": "JavaScript", "go": "Go",
    "c": "C", "shell": "Shell", "cpp": "C++", "rust": "Rust", "ruby": "Ruby",
    "php": "PHP", "sql": "SQL", "typescript": "TypeScript", "swift": "Swift",
    "kotlin": "Kotlin", "scala": "Scala", "r": "R", "dart": "Dart",
    "powershell": "PowerShell", "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "ibm-cloud": "IBM Cloud", "ai-ml": "AI/ML", "ai-manager": "AI Manager",
    "rag": "RAG Pipelines", "llm-dev": "LLM Development", "edge-ai": "Edge AI",
    "embedded": "Embedded Systems", "embedded-linux": "Embedded Linux",
    "embedded-python": "Embedded Python", "freertos": "FreeRTOS", "s32k": "S32K",
    "adobe": "Adobe Creative Cloud", "product-manager": "Product Manager",
    "product-lead": "Product Lead", "project-manager": "Project Manager",
    "servant-leadership": "Leadership & Management",
}


def load_questions() -> dict:
    if QUESTIONS_FILE.exists():
        return json.loads(QUESTIONS_FILE.read_text())
    return {}


def build_available_languages(questions: dict) -> dict:
    langs: dict[str, dict] = {}
    for script_path in sorted(SCRIPTS_DIR.glob("*.json")):
        lesson_id = script_path.stem
        try:
            script = json.loads(script_path.read_text())
        except json.JSONDecodeError:
            print(f"  ! skipping unparseable script: {script_path.name}")
            continue

        lang = script.get("language") or lesson_id.split("-")[0]
        source_urls = script.get("source_urls") or []
        video_file = f"{lesson_id}.mp4"

        lesson = {
            "id": lesson_id,
            "title": script.get("title", lesson_id),
            "description": script.get("description", ""),
            "video": video_file,
            # Renders are pruned after upload, so the app must tolerate a
            # lesson whose video is not currently hosted.
            "videoAvailable": (RENDERS_DIR / video_file).exists(),
            "sourceUrl": source_urls[0] if source_urls else "",
            "questions": questions.get(lesson_id, []),
        }
        langs.setdefault(lang, {
            "id": lang,
            "name": DISPLAY_NAMES.get(lang, lang.title()),
            "status": "available",
            "lessons": [],
        })["lessons"].append(lesson)
    return langs


def build_coming_soon_languages(available: dict) -> list[dict]:
    result = []
    if not DESKTOP_DIR.exists():
        return result
    for entry in sorted(DESKTOP_DIR.iterdir()):
        m = re.match(r"^(.+)-mastery-path$", entry.name)
        if not m:
            continue
        lang_id = m.group(1)
        if lang_id in available:
            continue
        result.append({
            "id": lang_id,
            "name": DISPLAY_NAMES.get(lang_id, lang_id.replace("-", " ").title()),
            "status": "coming_soon",
            "lessons": [],
        })
    return result


def main():
    questions = load_questions()
    available = build_available_languages(questions)
    coming_soon = build_coming_soon_languages(available)

    languages = sorted(available.values(), key=lambda l: l["name"]) + \
        sorted(coming_soon, key=lambda l: l["name"])

    manifest = {"schemaVersion": 2, "languages": languages}
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(manifest, indent=2))

    all_lessons = [les for l in languages for les in l["lessons"]]
    with_video = sum(1 for les in all_lessons if les["videoAvailable"])
    with_questions = sum(1 for les in all_lessons if les["questions"])
    total_questions = sum(len(les["questions"]) for les in all_lessons)

    print(f"Wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    print(f"  {len(available)} available languages, {len(coming_soon)} coming soon")
    print(f"  {len(all_lessons)} lessons; {with_video} with a local video, "
          f"{with_questions} with questions ({total_questions} questions total)")
    if with_video < len(all_lessons):
        print(f"  note: {len(all_lessons) - with_video} lessons have no local .mp4 "
              f"(pruned after YouTube upload) -- they will show as video-unavailable")


if __name__ == "__main__":
    main()
