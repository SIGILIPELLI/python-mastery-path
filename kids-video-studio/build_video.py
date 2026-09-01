"""
End-to-end: script JSON -> bilingual animated .mp4s.

For each language: synthesizes per-scene narration audio (voice/narrate_scene.py),
renders each scene's animation timed to that audio (render/record_scenes.py),
and muxes+concatenates into the final video (assemble/assemble.py).

Usage:
    video-studio/.venv/bin/python build_video.py content/scripts/kiko-tries-new-foods.json
"""
import json
import sys
from pathlib import Path

from render.scene_poses import SCENES
from render.record_scenes import record_scenes
from voice.narrate_scene import synthesize_scene
from assemble.assemble import assemble_video

ROOT = Path(__file__).parent
OUT_RENDERS = ROOT / "output" / "renders"
WORK_AUDIO = ROOT / "output" / "_work_audio"
WORK_CLIPS = ROOT / "output" / "_work_clips"


def build(script_path: Path, lang: str, vertical: bool = False):
    script = json.loads(script_path.read_text())
    scenes = script["scenes"]

    audio_dir = WORK_AUDIO / f"{script['id']}-{lang}"
    clip_dir = WORK_CLIPS / f"{script['id']}-{lang}"

    scene_specs = []
    audio_paths = []
    print(f"[{lang}] synthesizing narration for {len(scenes)} scenes...")
    for i, scene in enumerate(scenes):
        audio_path, duration_ms, line_timings = synthesize_scene(scene, lang, audio_dir, i)
        pose = SCENES[scene["scene_number"]]
        moral_text = None
        caption_lines = line_timings
        if not scene.get("dialogue"):
            moral_text = scene.get(f"on_screen_text_{lang}")
            caption_lines = []
        scene_specs.append({
            "scene_pose": pose,
            "caption_lines": caption_lines,
            "moral_text": moral_text,
            "duration_ms": duration_ms,
        })
        audio_paths.append(audio_path)
        print(f"  scene {i+1}/{len(scenes)}: {duration_ms}ms")

    print(f"[{lang}] rendering {len(scene_specs)} animated clips...")
    clip_paths = record_scenes(scene_specs, clip_dir, lang, vertical)

    out_path = OUT_RENDERS / f"{script['id']}-{lang}.mp4"
    print(f"[{lang}] muxing + concatenating -> {out_path}")
    assemble_video(clip_paths, audio_paths, out_path, vertical)

    for c in clip_paths:
        c.unlink()
    clip_dir.rmdir()
    for a in audio_paths:
        a.unlink()
    audio_dir.rmdir()

    print(f"[{lang}] done: {out_path}")
    return out_path


if __name__ == "__main__":
    script_path = Path(sys.argv[1])
    langs = sys.argv[2:] or ["en", "te"]
    for lang in langs:
        build(script_path, lang)
