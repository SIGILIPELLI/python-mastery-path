"""
Uploads a finished video to YouTube via the Data API v3.

First run: opens a browser tab, you log in as the channel's Google account
and click Allow -- this is a one-time step. The resulting refresh token is
cached to credentials/token.json (gitignored) so future runs don't need to
re-authenticate.

This module never runs unattended as part of make_video.py -- it is only
ever invoked explicitly, per the "confirm before publishing" rule.

Usage (library):
    from upload.youtube_upload import upload_video
    video_id = upload_video(
        "output/renders/my-video.mp4",
        title="...", description="...", tags=[...],
        privacy_status="private",  # "private" | "unlisted" | "public"
    )
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube"]  # upload + list/update own videos' status
CREDS_DIR = Path(__file__).resolve().parents[1] / "credentials"
CLIENT_SECRET_PATH = CREDS_DIR / "client_secret.json"
TOKEN_PATH = CREDS_DIR / "token.json"


def _get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                raise FileNotFoundError(
                    f"Missing {CLIENT_SECRET_PATH} -- download it from "
                    "Google Cloud Console > APIs & Services > Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
    category_id: str = "27",  # "27" = Education
) -> str:
    """Uploads video_path to the authenticated channel. Returns the new video ID."""
    assert privacy_status in ("private", "unlisted", "public"), privacy_status

    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  uploading... {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://youtube.com/watch?v={video_id} (privacy: {privacy_status})")
    return video_id
