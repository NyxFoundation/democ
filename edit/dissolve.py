"""Render short cross-dissolves as editable clips shared by MLT and Kdenlive."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


def bridge(left: Path, right: Path, *, left_frames: int, frames: int,
           fps: int, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    sources = [(str(p.resolve()), p.stat().st_mtime_ns, p.stat().st_size)
               for p in (left, right)]
    signature = json.dumps([sources, left_frames, frames, fps, "dissolve-v4-ease-range"])
    key = hashlib.sha256(signature.encode()).hexdigest()[:16]
    path = directory / f"dissolve-{key}.mp4"
    if path.exists():
        return path
    seconds = frames / fps
    start = (left_frames - frames) / fps
    # Chromium is full-range; Blender is limited-range. Normalize before mixing
    # and tag the result, otherwise the boundary can flash darker or brighter.
    normalize = ("scale=in_range=auto:out_range=pc:out_color_matrix=bt601,"
                 "format=yuv420p,setparams=range=full:colorspace=bt470bg")
    graph = (
        f"[0:v]fps={fps},trim=duration={seconds},settb=AVTB,setpts=PTS-STARTPTS,{normalize}[a];"
        f"[1:v]fps={fps},trim=duration={seconds},settb=AVTB,setpts=PTS-STARTPTS,{normalize}[b];"
        f"[a][b]xfade=transition=custom:duration={seconds}:offset=0:"
        "expr='A*(P*P*(3-2*P))+B*(1-P*P*(3-2*P))',format=yuv420p[v]"
    )
    temporary = path.with_suffix(".tmp.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-filter_complex_threads", "1",
            "-ss", str(start), "-i", str(left), "-i", str(right),
            "-filter_complex", graph, "-map", "[v]", "-frames:v", str(frames),
            "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-color_range", "pc", "-colorspace", "bt470bg",
            "-movflags", "+faststart", str(temporary),
        ], check=True)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def splice(clips: list[dict], *, seconds: float, fps: int, directory: Path) -> list[dict]:
    """Use each source frame once: body, overlapped tails/heads, next body."""
    if seconds <= 0 or len(clips) < 2:
        return clips
    frames = max(round(seconds * fps), 1)
    if any(c["frames"] <= 2 * frames for c in clips):
        raise ValueError("A scene is too short for the requested transition")
    result = []
    for i, source in enumerate(clips):
        head = frames if i else 0
        tail = frames if i < len(clips) - 1 else 0
        body = dict(source)
        body.update({"in": source.get("in", 0) + head,
                     "frames": source["frames"] - head - tail,
                     "fade_in": source.get("fade_in", 0) if not i else 0,
                     "fade_out": source.get("fade_out", 0) if not tail else 0})
        result.append(body)
        if tail:
            nxt = clips[i + 1]
            path = bridge(source["path"], nxt["path"],
                          left_frames=source["frames"], frames=frames,
                          fps=fps, directory=directory)
            result.append({"path": path, "name": f"{source['name']} → {nxt['name']}",
                           "in": 0, "frames": frames, "fade_in": 0, "fade_out": 0})
    return result
