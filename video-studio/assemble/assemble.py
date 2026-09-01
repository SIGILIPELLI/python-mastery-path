"""
Muxes each beat's narration audio into its rendered .webm clip, transcodes to
h264/aac mp4 (YouTube's preferred format -- Playwright only outputs vp8/webm),
and concatenates all beats into the final video.

Usage (library):
    from assemble.assemble import assemble_video
    final_path = assemble_video(clip_paths, audio_paths, out_path, vertical=True)
"""
import subprocess
from pathlib import Path

VERTICAL_SIZE = "1080:1920"
HORIZONTAL_SIZE = "1920:1080"


def _mux_one(clip_path: Path, audio_path: Path, out_path: Path, size: str):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(clip_path),
            "-i", str(audio_path),
            "-vf", f"scale={size}:force_original_aspect_ratio=decrease,pad={size}:(ow-iw)/2:(oh-ih)/2,fps=30",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
            "-shortest",
            str(out_path),
        ],
        check=True, capture_output=True, text=True,
    )


def assemble_video(clip_paths: list[Path], audio_paths: list[Path], out_path: Path, vertical: bool) -> Path:
    assert len(clip_paths) == len(audio_paths), "clip_paths and audio_paths must be the same length"
    size = VERTICAL_SIZE if vertical else HORIZONTAL_SIZE
    work_dir = out_path.parent / f"_mux_{out_path.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    muxed = []
    for idx, (clip, audio) in enumerate(zip(clip_paths, audio_paths)):
        muxed_path = work_dir / f"muxed_{idx:02d}.mp4"
        try:
            _mux_one(clip, audio, muxed_path, size)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg mux failed on beat {idx}: {e.stderr}") from e
        muxed.append(muxed_path)

    concat_list = work_dir / "concat.txt"
    concat_list.write_text("\n".join(f"file '{p.resolve()}'" for p in muxed))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(out_path),
        ],
        check=True, capture_output=True, text=True,
    )

    for p in muxed:
        p.unlink()
    concat_list.unlink()
    work_dir.rmdir()

    return out_path
