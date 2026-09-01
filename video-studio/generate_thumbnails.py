"""
Renders a custom 1280x720 thumbnail per pipeline video and saves it to
output/thumbnails/<video_id>.jpg. Does not upload -- that's a separate step
(upload/set_thumbnails.py) so a bad render never risks touching YouTube.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from render.thumbnail_template import render_thumbnail_html

OUT_DIR = Path(__file__).parent / "output" / "thumbnails"


def generate(video_map: list[dict]):
    """video_map: [{"id": ..., "title": ..., "language": ...}, ...]"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
        page = context.new_page()
        for v in video_map:
            html = render_thumbnail_html(v["title"], v["language"])
            page.set_content(html)
            out_path = OUT_DIR / f"{v['id']}.jpg"
            page.screenshot(path=str(out_path), type="jpeg", quality=92)
            print("wrote", out_path)
        browser.close()


if __name__ == "__main__":
    import sys
    video_map = json.loads(Path(sys.argv[1]).read_text())
    generate(video_map)
