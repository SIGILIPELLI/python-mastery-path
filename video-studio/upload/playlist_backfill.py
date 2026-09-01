#!/usr/bin/env python3
"""
One-time backfill: creates one YouTube playlist per Mastery Path subject and
adds every already-published video to its matching playlist, sorted oldest
first (roughly Level 1 -> Level 4 order).

Classification source: each video's description ends with a
"Source lesson(s): https://sigilipelli.github.io/<language>-mastery-path/..."
link (or, for Product Manager, a product-manager-path URL) -- that's the
ground truth used to bucket videos, not the title.

Resumable: progress (playlist ids created + video ids already added) is
persisted to output/playlist_backfill_progress.json after every single API
call, so a YouTube API quotaExceeded error (or any crash) can be re-run
later with `--resume` and it picks up exactly where it left off, spending
zero extra quota re-doing completed work.

Usage:
    .venv/bin/python upload/playlist_backfill.py            # run/resume
    .venv/bin/python upload/playlist_backfill.py --dry-run   # just print the plan
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CREDS_DIR = Path(__file__).resolve().parents[1] / "credentials"
TOKEN_PATH = CREDS_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]

PROGRESS_PATH = Path(__file__).resolve().parents[1] / "output" / "playlist_backfill_progress.json"

# Excluded: pre-existing personal videos on the channel unrelated to Mastery Path.
EXCLUDE_VIDEO_IDS = {"iZ0InDMMEWQ", "naXOhhu8XGs", "F3YEA7st4DY", "aRJ9G5dSN0I"}

LANG_MAP = {
    "python-mastery-path": "Python Mastery Path",
    "java-mastery-path": "Java Mastery Path",
    "javascript-mastery-path": "JavaScript Mastery Path",
    "shell-mastery-path": "Bash/Shell Mastery Path",
    "bash-mastery-path": "Bash/Shell Mastery Path",
    "c-mastery-path": "C Mastery Path",
    "cpp-mastery-path": "C++ Mastery Path",
    "go-mastery-path": "Go Mastery Path",
    "sql-mastery-path": "SQL Mastery Path",
    "typescript-mastery-path": "TypeScript Mastery Path",
    "ruby-mastery-path": "Ruby Mastery Path",
    "php-mastery-path": "PHP Mastery Path",
    "product-manager": "Product Manager Path",
}
URL_RE = re.compile(r"sigilipelli\.github\.io/([a-z0-9\-]+)/")

PLAYLIST_DESCRIPTIONS = {
    "Python Mastery Path": "All Python Mastery Path videos from sigilipelli.github.io/python-mastery-path, in level order.",
    "Java Mastery Path": "All Java Mastery Path videos from sigilipelli.github.io/java-mastery-path, in level order.",
    "JavaScript Mastery Path": "All JavaScript Mastery Path videos from sigilipelli.github.io/javascript-mastery-path, in level order.",
    "Bash/Shell Mastery Path": "All Bash/Shell Mastery Path videos from sigilipelli.github.io/shell-mastery-path, in level order.",
    "C Mastery Path": "All C Mastery Path videos from sigilipelli.github.io/c-mastery-path, in level order.",
    "C++ Mastery Path": "All C++ Mastery Path videos from sigilipelli.github.io/cpp-mastery-path, in level order.",
    "Go Mastery Path": "All Go Mastery Path videos from sigilipelli.github.io/go-mastery-path, in level order.",
    "SQL Mastery Path": "All SQL Mastery Path videos from sigilipelli.github.io/sql-mastery-path, in level order.",
    "TypeScript Mastery Path": "All TypeScript Mastery Path videos from sigilipelli.github.io/typescript-mastery-path, in level order.",
    "Ruby Mastery Path": "All Ruby Mastery Path videos from sigilipelli.github.io/ruby-mastery-path, in level order.",
    "PHP Mastery Path": "All PHP Mastery Path videos from sigilipelli.github.io/php-mastery-path, in level order.",
    "Product Manager Path": "All Product Manager Path videos, in level order.",
}

# Playlists already created by hand before this script existed -- reuse, don't recreate.
KNOWN_PLAYLIST_IDS = {
    "Java Mastery Path": "PLKFSE9THU0JE",
}


def get_youtube():
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def fetch_all_videos(youtube):
    ch = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_playlist_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ids = []
    page_token = None
    while True:
        resp = youtube.playlistItems().list(
            part="contentDetails", playlistId=uploads_playlist_id, maxResults=50, pageToken=page_token
        ).execute()
        for item in resp["items"]:
            vid = item["contentDetails"]["videoId"]
            if vid not in ids:
                ids.append(vid)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    full = []
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        resp = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
        for item in resp["items"]:
            full.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "published_at": item["snippet"]["publishedAt"],
            })
    return full


def classify(videos):
    buckets = {}
    unmatched = []
    for v in videos:
        if v["video_id"] in EXCLUDE_VIDEO_IDS:
            continue
        matched = None
        for slug in URL_RE.findall(v["description"]):
            for prefix, name in LANG_MAP.items():
                if slug.startswith(prefix):
                    matched = name
                    break
            if matched:
                break
        if matched:
            buckets.setdefault(matched, []).append(v)
        else:
            unmatched.append(v)
    for name in buckets:
        buckets[name].sort(key=lambda v: v["published_at"])
    return buckets, unmatched


def call_with_retry(fn, max_retries=5, base_delay=20):
    """Retries on RATE_LIMIT_EXCEEDED / quotaExceeded 429s with exponential backoff.
    Re-raises immediately on anything else, or once retries are exhausted."""
    for attempt in range(max_retries):
        try:
            return fn()
        except HttpError as e:
            transient = "RATE_LIMIT_EXCEEDED" in str(e) or "rateLimitExceeded" in str(e)
            if not transient or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"  rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)


def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text())
    return {}


def save_progress(progress):
    PROGRESS_PATH.write_text(json.dumps(progress, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the plan, make no API writes")
    args = parser.parse_args()

    youtube = get_youtube()
    print("Fetching full channel video list + descriptions...")
    videos = fetch_all_videos(youtube)
    buckets, unmatched = classify(videos)

    print(f"\n{len(videos)} total videos on channel. Classified into {len(buckets)} subjects, {len(unmatched)} unmatched.")
    if unmatched:
        print("Unmatched (left alone, not added to any playlist):")
        for v in unmatched:
            print(f"  - {v['title']} ({v['video_id']})")

    # Process smallest buckets first so more subjects finish fully before any quota cutoff.
    order = sorted(buckets, key=lambda k: len(buckets[k]))

    if args.dry_run:
        print("\n--- DRY RUN PLAN ---")
        for name in order:
            print(f"{name}: {len(buckets[name])} videos")
        return

    progress = load_progress()

    for name in order:
        entry = progress.setdefault(name, {"playlist_id": KNOWN_PLAYLIST_IDS.get(name), "added": []})
        vids = buckets[name]
        remaining = [v for v in vids if v["video_id"] not in entry["added"]]
        if not remaining and entry["playlist_id"]:
            print(f"[{name}] already fully populated ({len(vids)} videos). Skipping.")
            continue

        if not entry["playlist_id"]:
            print(f"[{name}] creating playlist...")
            try:
                body = {
                    "snippet": {
                        "title": name,
                        "description": PLAYLIST_DESCRIPTIONS.get(name, f"All {name} videos, in level order."),
                    },
                    "status": {"privacyStatus": "public"},
                }
                resp = call_with_retry(lambda: youtube.playlists().insert(part="snippet,status", body=body).execute())
                entry["playlist_id"] = resp["id"]
                save_progress(progress)
                print(f"[{name}] created playlist {resp['id']}")
            except HttpError as e:
                print(f"[{name}] FAILED to create playlist: {e}")
                if "quotaExceeded" in str(e) or "RATE_LIMIT_EXCEEDED" in str(e):
                    print("\nQuota/rate limit exceeded (retries exhausted). Progress saved. Re-run this script later to resume.")
                    save_progress(progress)
                    return
                raise

        for v in remaining:
            try:
                item_body = {
                    "snippet": {
                        "playlistId": entry["playlist_id"],
                        "resourceId": {"kind": "youtube#video", "videoId": v["video_id"]},
                    }
                }
                call_with_retry(lambda: youtube.playlistItems().insert(part="snippet", body=item_body).execute())
                entry["added"].append(v["video_id"])
                save_progress(progress)
                print(f"[{name}] added: {v['title']}")
            except HttpError as e:
                print(f"[{name}] FAILED to add {v['title']}: {e}")
                if "quotaExceeded" in str(e) or "RATE_LIMIT_EXCEEDED" in str(e):
                    print("\nQuota/rate limit exceeded (retries exhausted). Progress saved. Re-run this script later to resume.")
                    save_progress(progress)
                    return
                raise

        print(f"[{name}] done -- {len(entry['added'])}/{len(vids)} videos in playlist.")

    print("\nAll subjects fully populated.")


if __name__ == "__main__":
    main()
