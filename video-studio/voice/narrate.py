"""
Generates narration audio per beat using edge-tts -- a free neural TTS
engine (same voices as Azure Neural TTS) with genuinely human-sounding,
non-robotic voices. Default is a warm, polite female voice.

Usage (library):
    from voice.narrate import synthesize_script
    audio_paths, durations_ms = synthesize_script(script["beats"], out_dir, voice="en-US-JennyNeural")
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_RATE = "-6%"    # a touch slower than default -- calmer, more human, less "read aloud"
DEFAULT_PITCH = "+0Hz"


async def _synthesize_one(text: str, voice: str, rate: str, out_mp3: Path):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=DEFAULT_PITCH)
    await communicate.save(str(out_mp3))


def _probe_duration_ms(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(out.stdout.strip()) * 1000)


def synthesize_script(beats: list[dict], out_dir: Path, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE):
    """Synthesizes one mp3 per beat. Returns (audio_paths, durations_ms), both
    ordered to match `beats`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_paths = []
    durations_ms = []

    for idx, beat in enumerate(beats):
        text = beat["narration"].strip()
        out_mp3 = out_dir / f"beat_{idx:02d}.mp3"
        asyncio.run(_synthesize_one(text, voice, rate, out_mp3))
        audio_paths.append(out_mp3)
        durations_ms.append(_probe_duration_ms(out_mp3))

    return audio_paths, durations_ms
