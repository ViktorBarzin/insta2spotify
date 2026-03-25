import asyncio
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from shazamio import Shazam

logger = logging.getLogger(__name__)

@dataclass
class ShazamResult:
    song: str
    artist: str
    shazam_id: str

async def split_audio(audio_path: str, segment_duration: int, overlap: int, output_dir: str) -> list[str]:
    """Split audio into overlapping segments using ffmpeg."""
    duration_proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await duration_proc.communicate()
    total_duration = float(stdout.decode().strip())

    segments = []
    step = segment_duration - overlap
    start = 0
    idx = 0
    while start < total_duration:
        segment_path = f"{output_dir}/segment_{idx}.mp3"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", audio_path,
            "-ss", str(start), "-t", str(segment_duration),
            "-acodec", "libmp3lame", "-q:a", "2",
            segment_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode == 0:
            segments.append(segment_path)
        start += step
        idx += 1

    return segments

async def identify_segment(shazam: Shazam, segment_path: str) -> ShazamResult | None:
    try:
        result = await shazam.recognize(segment_path)
        matches = result.get("matches", [])
        if not matches:
            return None
        track = result.get("track", {})
        if not track:
            return None
        return ShazamResult(
            song=track.get("title", ""),
            artist=track.get("subtitle", ""),
            shazam_id=track.get("key", ""),
        )
    except Exception as e:
        logger.warning("Shazam failed on %s: %s", segment_path, e)
        return None

async def identify_songs(audio_path: str, segment_duration: int = 15, overlap: int = 5) -> list[ShazamResult]:
    """Identify all songs in an audio file by splitting into segments."""
    import tempfile
    work_dir = tempfile.mkdtemp(prefix="shazam_")

    segments = await split_audio(audio_path, segment_duration, overlap, work_dir)
    if not segments:
        # Try the whole file
        segments = [audio_path]

    shazam = Shazam()
    tasks = [identify_segment(shazam, seg) for seg in segments]
    results = await asyncio.gather(*tasks)

    # Deduplicate by shazam_id
    seen = set()
    unique = []
    for r in results:
        if r and r.shazam_id not in seen:
            seen.add(r.shazam_id)
            unique.append(r)

    return unique
