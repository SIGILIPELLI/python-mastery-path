"""
Records each scene's HTML (render/scene_template.py) to its own .webm clip
using headless Chromium via Playwright, synced to that scene's narration
duration. Same technique as the coding-tutorial pipeline's render/record.py.
"""
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

from render.scene_template import render_scene_html, VERTICAL_SIZE, HORIZONTAL_SIZE


def record_scenes(scene_specs: list[dict], out_dir: Path, lang: str, vertical: bool) -> list[Path]:
    """scene_specs: list of {scene_pose, caption_lines, moral_text, duration_ms}.
    Returns ordered list of clip paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    size = VERTICAL_SIZE if vertical else HORIZONTAL_SIZE
    clip_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for idx, spec in enumerate(scene_specs):
            html = render_scene_html(
                spec["scene_pose"], spec["caption_lines"], spec["moral_text"],
                lang, vertical,
            )
            video_dir = out_dir / f"_tmp_{idx:02d}"
            video_dir.mkdir(exist_ok=True)
            context = browser.new_context(
                viewport=size,
                record_video_dir=str(video_dir),
                record_video_size=size,
            )
            page = context.new_page()
            page.set_content(html)
            page.wait_for_timeout(spec["duration_ms"])
            page.close()
            context.close()

            produced = list(video_dir.glob("*.webm"))
            assert produced, f"Playwright didn't produce a video for scene {idx}"
            final_path = out_dir / f"scene_{idx:02d}.webm"
            shutil.move(str(produced[0]), str(final_path))
            shutil.rmtree(video_dir)
            clip_paths.append(final_path)
        browser.close()

    return clip_paths
