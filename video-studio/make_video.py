#!/usr/bin/env python3
"""
Orchestrator: takes a script JSON (written by the yt-shorts-writer or
yt-longform-producer subagent) and produces a finished MP4 + a metadata file
with the title/description/tags/source links -- ready for the user to review
and upload themselves. This pipeline never publishes anything; publishing to
YouTube is always a manual, explicit step.

Usage:
    .venv/bin/python make_video.py --script output/scripts/python-level-1-03-control-flow-short.json
    .venv/bin/python make_video.py --script output/scripts/exceptions-longform.json --out output/renders/exceptions.mp4
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice.narrate import synthesize_script
from render.record import render_beats
from assemble.assemble import assemble_video

REQUIRED_TOP_KEYS = {"type", "title", "description", "tags", "voice", "source_urls", "beats"}


def load_script(script_path: Path) -> dict:
    data = json.loads(script_path.read_text())
    missing = REQUIRED_TOP_KEYS - data.keys()
    if missing:
        raise ValueError(f"Script JSON is missing required keys: {missing}")
    if data["type"] not in ("short", "longform"):
        raise ValueError(f"Unknown script type: {data['type']!r} (must be 'short' or 'longform')")
    if not data["beats"]:
        raise ValueError("Script has no beats")
    for i, beat in enumerate(data["beats"]):
        if "narration" not in beat or "display" not in beat:
            raise ValueError(f"Beat {i} is missing 'narration' or 'display'")
    return data


def write_metadata(script: dict, out_path: Path):
    lines = [
        f"Title: {script['title']}",
        "",
        "Description:",
        script["description"],
        "",
        "Tags: " + ", ".join(script["tags"]),
        "",
        "Source lesson(s):",
        *[f"- {u}" for u in script["source_urls"]],
    ]
    out_path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path, help="Path to a script JSON from yt-shorts-writer or yt-longform-producer")
    parser.add_argument("--out", type=Path, default=None, help="Output mp4 path (default: output/renders/<script-stem>.mp4)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate audio/video clip files for inspection")
    args = parser.parse_args()

    if not args.script.is_file():
        sys.exit(f"Script file not found: {args.script}")

    script = load_script(args.script)
    vertical = script["type"] == "short"

    out_path = args.out or (Path(__file__).parent / "output" / "renders" / f"{args.script.stem}.mp4")
    work_root = Path(__file__).parent / "output" / "_work" / args.script.stem

    print(f"[1/3] Synthesizing narration ({script['voice']}) for {len(script['beats'])} beats...")
    audio_paths, durations_ms = synthesize_script(script["beats"], work_root / "audio", voice=script["voice"])
    total_s = sum(durations_ms) / 1000
    print(f"      -> total narration: {total_s:.1f}s across {len(audio_paths)} beats")

    print(f"[2/3] Rendering {'vertical (Shorts)' if vertical else 'horizontal (long-form)'} animation clips...")
    clip_paths = render_beats(script["beats"], durations_ms, work_root / "clips", vertical=vertical)

    print("[3/3] Muxing audio + video and assembling final MP4...")
    final_path = assemble_video(clip_paths, audio_paths, out_path, vertical=vertical)

    metadata_path = out_path.with_suffix(".metadata.txt")
    write_metadata(script, metadata_path)

    if not args.keep_temp:
        import shutil
        shutil.rmtree(work_root, ignore_errors=True)

    print()
    print(f"Done. Video:    {final_path}")
    print(f"      Metadata: {metadata_path}  (title/description/tags/source links -- for you to review before uploading)")
    print(f"      Runtime:  ~{total_s:.0f}s")


if __name__ == "__main__":
    main()
