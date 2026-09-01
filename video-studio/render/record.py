"""
Renders each beat of a video script to its own .webm clip using a headless
Chromium tab (Playwright's built-in video recording) -- this is the
"simulated screen recording" of code typing/running, fully scripted, no
human capture needed.

Usage (library):
    from render.record import render_beats
    clip_paths = render_beats(beats, durations_ms, out_dir, vertical=True)
"""
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

from render.beat_template import render_beat_html

VERTICAL_SIZE = {"width": 1080, "height": 1920}
HORIZONTAL_SIZE = {"width": 1920, "height": 1080}


def render_beats(beats: list[dict], durations_ms: list[int], out_dir: Path, vertical: bool) -> list[Path]:
    """Renders one .webm per beat, synced to that beat's narration duration.
    Returns the ordered list of clip paths (out_dir/beat_00.webm, ...).
    """
    assert len(beats) == len(durations_ms), "beats and durations_ms must be the same length"
    out_dir.mkdir(parents=True, exist_ok=True)
    size = VERTICAL_SIZE if vertical else HORIZONTAL_SIZE
    clip_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for idx, (beat, dur_ms) in enumerate(zip(beats, durations_ms)):
            video_dir = out_dir / f"_tmp_{idx:02d}"
            video_dir.mkdir(exist_ok=True)
            context = browser.new_context(
                viewport=size,
                record_video_dir=str(video_dir),
                record_video_size=size,
            )
            page = context.new_page()
            html = render_beat_html(beat, dur_ms, vertical)
            page.set_content(html)
            page.wait_for_timeout(dur_ms)
            page.close()
            context.close()  # flushes the video file to disk

            produced = list(video_dir.glob("*.webm"))
            assert produced, f"Playwright didn't produce a video for beat {idx}"
            final_path = out_dir / f"beat_{idx:02d}.webm"
            shutil.move(str(produced[0]), str(final_path))
            shutil.rmtree(video_dir)
            clip_paths.append(final_path)
        browser.close()

    return clip_paths
