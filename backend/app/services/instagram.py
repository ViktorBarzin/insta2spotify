import asyncio
import json
import logging
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InstagramData:
    title: str | None = None
    artist: str | None = None
    track: str | None = None
    audio_path: str | None = None
    video_path: str | None = None
    duration: float = 0

async def extract_metadata(url: str) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "--dump-json", "--no-download", url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("yt-dlp metadata failed: %s", stderr.decode())
        return {}
    return json.loads(stdout.decode())

async def download_audio(url: str, output_dir: str) -> str | None:
    output_path = f"{output_dir}/audio.%(ext)s"
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", output_path, url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("yt-dlp download failed: %s", stderr.decode())
        return None
    # Find the downloaded file
    import glob
    files = glob.glob(f"{output_dir}/audio.*")
    return files[0] if files else None

async def download_video(url: str, output_dir: str) -> str | None:
    output_path = f"{output_dir}/video.%(ext)s"
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "-o", output_path, url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("yt-dlp video download failed: %s", stderr.decode())
        return None
    import glob
    files = glob.glob(f"{output_dir}/video.*")
    return files[0] if files else None

async def get_instagram_data(url: str, work_dir: str) -> InstagramData:
    metadata = await extract_metadata(url)
    data = InstagramData(
        title=metadata.get("title"),
        artist=metadata.get("artist") or metadata.get("creator") or metadata.get("uploader"),
        track=metadata.get("track"),
        duration=metadata.get("duration", 0),
    )
    data.audio_path = await download_audio(url, work_dir)
    data.video_path = await download_video(url, work_dir)
    return data
