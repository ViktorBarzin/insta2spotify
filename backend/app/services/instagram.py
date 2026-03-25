import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger(__name__)

def _ytdlp_base_args() -> list[str]:
    """Common yt-dlp args for Instagram access."""
    settings = get_settings()
    args = [
        "yt-dlp",
        "--no-check-certificates",
        "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]
    if os.path.exists(settings.instagram_cookies_path):
        args.extend(["--cookies", settings.instagram_cookies_path])
    return args

@dataclass
class InstagramData:
    title: str | None = None
    artist: str | None = None
    track: str | None = None
    audio_path: str | None = None
    video_path: str | None = None
    duration: float = 0

async def extract_metadata(url: str) -> dict:
    args = _ytdlp_base_args() + ["--dump-json", "--no-download", url]
    proc = await asyncio.create_subprocess_exec(
        *args,
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
    args = _ytdlp_base_args() + ["-x", "--audio-format", "mp3", "-o", output_path, url]
    proc = await asyncio.create_subprocess_exec(
        *args,
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
    args = _ytdlp_base_args() + ["-o", output_path, url]
    proc = await asyncio.create_subprocess_exec(
        *args,
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
