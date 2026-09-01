"""
Synthesizes one audio track per scene from its dialogue lines (or, for a
dialogue-free scene, its on-screen moral text), using a distinct free
edge-tts voice per character so kids can tell who's talking. Lines are
joined with short silence gaps; the whole track gets a little lead-in/tail
padding so captions and animation have room to fade.

Usage:
    from voice.narrate_scene import synthesize_scene
    audio_path, total_ms, line_timings = synthesize_scene(scene, lang, out_dir, idx)
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

VOICES = {
    "en": {"kiko": "en-US-AnaNeural", "bibbo": "en-US-EmmaNeural", "narrator": "en-US-JennyNeural"},
    "te": {"kiko": "te-IN-MohanNeural", "bibbo": "te-IN-ShrutiNeural", "narrator": "te-IN-ShrutiNeural"},
}
RATE = "-8%"
LEAD_MS = 250
GAP_MS = 450
TAIL_MS = 750


async def _synthesize_one(text: str, voice: str, out_mp3: Path):
    communicate = edge_tts.Communicate(text, voice=voice, rate=RATE)
    await communicate.save(str(out_mp3))


def _probe_duration_ms(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(out.stdout.strip()) * 1000)


def _silence(out_path: Path, ms: int):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
         "-t", str(ms / 1000), "-q:a", "9", str(out_path)],
        check=True, capture_output=True, text=True,
    )


def synthesize_scene(scene: dict, lang: str, out_dir: Path, idx: int):
    """Returns (audio_path, total_ms, line_timings) where line_timings is a
    list of {speaker, text, start_ms, dur_ms} for caption sync.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    voices = VOICES[lang]
    work = out_dir / f"_parts_{idx:02d}"
    work.mkdir(exist_ok=True)

    pieces = []  # ordered list of (path, is_gap)
    line_timings = []

    lead_path = work / "lead.mp3"
    _silence(lead_path, LEAD_MS)
    pieces.append(lead_path)
    cursor_ms = LEAD_MS

    dialogue = scene.get("dialogue", [])
    if dialogue:
        for i, line in enumerate(dialogue):
            speaker = line["character"]
            text = line[f"line_{lang}"].strip()
            voice = voices.get(speaker, voices["narrator"])
            line_mp3 = work / f"line_{i:02d}.mp3"
            asyncio.run(_synthesize_one(text, voice, line_mp3))
            dur = _probe_duration_ms(line_mp3)
            line_timings.append({"speaker": speaker, "text": text, "start_ms": cursor_ms, "dur_ms": dur})
            pieces.append(line_mp3)
            cursor_ms += dur
            if i < len(dialogue) - 1:
                gap_path = work / f"gap_{i:02d}.mp3"
                _silence(gap_path, GAP_MS)
                pieces.append(gap_path)
                cursor_ms += GAP_MS
    else:
        text = scene.get(f"on_screen_text_{lang}") or ""
        moral_mp3 = work / "moral.mp3"
        asyncio.run(_synthesize_one(text, voices["narrator"], moral_mp3))
        dur = _probe_duration_ms(moral_mp3)
        line_timings.append({"speaker": "narrator", "text": text, "start_ms": cursor_ms, "dur_ms": dur})
        pieces.append(moral_mp3)
        cursor_ms += dur

    tail_path = work / "tail.mp3"
    _silence(tail_path, TAIL_MS)
    pieces.append(tail_path)
    cursor_ms += TAIL_MS

    concat_list = work / "concat.txt"
    concat_list.write_text("\n".join(f"file '{p.resolve()}'" for p in pieces))
    out_path = out_dir / f"scene_{idx:02d}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c:a", "libmp3lame", "-q:a", "2", str(out_path)],
        check=True, capture_output=True, text=True,
    )
    total_ms = _probe_duration_ms(out_path)

    for p in pieces:
        p.unlink()
    concat_list.unlink()
    work.rmdir()

    return out_path, total_ms, line_timings
