import asyncio
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OCRSong:
    song: str
    artist: str

async def extract_frames(video_path: str, output_dir: str, num_frames: int = 3) -> list[str]:
    """Extract frames at 25%, 50%, 75% of video duration."""
    # Get duration
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    duration = float(stdout.decode().strip())

    frames = []
    positions = [0.25, 0.50, 0.75]
    for i, pos in enumerate(positions[:num_frames]):
        timestamp = duration * pos
        frame_path = f"{output_dir}/frame_{i}.png"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
            "-vframes", "1", "-vf", "crop=iw:ih*0.3:0:ih*0.7",
            frame_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode == 0:
            frames.append(frame_path)
    return frames

def parse_song_text(texts: list[str]) -> list[OCRSong]:
    """Parse OCR text for song/artist patterns."""
    songs = []
    for text in texts:
        # Pattern: "Artist - Song" or "Song - Artist"
        match = re.match(r'^(.+?)\s*[-–—]\s*(.+)$', text.strip())
        if match:
            part1, part2 = match.group(1).strip(), match.group(2).strip()
            if len(part1) > 1 and len(part2) > 1:
                songs.append(OCRSong(artist=part1, song=part2))
    return songs

async def identify_songs_ocr(video_path: str) -> list[OCRSong]:
    """Extract and OCR video frames to find song information."""
    import tempfile
    work_dir = tempfile.mkdtemp(prefix="ocr_")

    frames = await extract_frames(video_path, work_dir)
    if not frames:
        return []

    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
    except Exception as e:
        logger.warning("EasyOCR not available: %s", e)
        return []

    all_texts = []
    for frame in frames:
        try:
            results = reader.readtext(frame)
            all_texts.extend([text for _, text, conf in results if conf > 0.5])
        except Exception as e:
            logger.warning("OCR failed on %s: %s", frame, e)

    return parse_song_text(all_texts)
