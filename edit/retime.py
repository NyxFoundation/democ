"""Cache a scene's playback speed for the video edit, preserving its source master."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess


def video(source: Path, *, speed: float, duration: float,
          fps: int, directory: Path) -> Path:
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError("Scene speed must be a positive finite number")
    if speed == 1:
        return source
    directory.mkdir(parents=True, exist_ok=True)
    signature = json.dumps([str(source.resolve()), source.stat().st_mtime_ns,
                            source.stat().st_size, speed, duration, fps, "retime-v1"])
    key = hashlib.sha256(signature.encode()).hexdigest()[:16]
    path = directory / f"{source.stem}-{key}.mp4"
    if path.exists():
        return path
    temporary = path.with_suffix(".tmp.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-vf", f"setpts=(PTS-STARTPTS)/{speed},fps={fps}",
            "-frames:v", str(max(1, round(duration / speed * fps))),
            "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary),
        ], check=True)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path
