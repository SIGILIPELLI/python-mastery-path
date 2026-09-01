#!/usr/bin/env python3
"""
Uploads an already-rendered video to YouTube, pulling title/description/tags
from its script JSON. Defaults to "public" (per the channel owner's
decision to publish for real views) -- this script is only ever run after
an explicit go-ahead in chat for that day's batch, never on an unattended
schedule. Use --privacy private/unlisted to override for one-off drafts.

Usage:
    .venv/bin/python upload/upload_cli.py --script output/scripts/<name>.json
    .venv/bin/python upload/upload_cli.py --script output/scripts/<name>.json --privacy private
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from upload.youtube_upload import upload_video


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--video", type=Path, default=None, help="Override path to the rendered mp4 (default: output/renders/<script-stem>.mp4)")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default="public")
    args = parser.parse_args()

    script = json.loads(args.script.read_text())
    video_path = args.video or (Path(__file__).parent.parent / "output" / "renders" / f"{args.script.stem}.mp4")

    if not video_path.is_file():
        sys.exit(f"Rendered video not found: {video_path} (run make_video.py first)")

    print(f"Uploading {video_path.name} as {args.privacy}...")
    print(f"  Title: {script['title']}")
    upload_video(
        str(video_path),
        title=script["title"],
        description=script["description"],
        tags=script["tags"],
        privacy_status=args.privacy,
    )


if __name__ == "__main__":
    main()
