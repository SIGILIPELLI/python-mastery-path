#!/usr/bin/env python3
"""
Sets a custom thumbnail on an already-uploaded video via the YouTube Data API.

Usage:
    .venv/bin/python upload/set_thumbnail.py --video-id <id> --image output/thumbnails/<name>.jpg
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from upload.youtube_upload import _get_credentials


def set_thumbnail(video_id: str, image_path: str):
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    media = MediaFileUpload(image_path, mimetype="image/jpeg")
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f"Thumbnail set for https://youtube.com/watch?v={video_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--image", required=True, type=Path)
    args = parser.parse_args()

    if not args.image.is_file():
        sys.exit(f"Thumbnail not found: {args.image}")

    set_thumbnail(args.video_id, str(args.image))


if __name__ == "__main__":
    main()
