import logging
import tempfile
from difflib import SequenceMatcher
from dataclasses import dataclass

from app.config import get_settings
from app.services.instagram import get_instagram_data
from app.services.fingerprint import identify_songs as shazam_identify
from app.services.ocr import identify_songs_ocr
from app.services.spotify import search_track, add_to_playlist, get_playlist_track_ids

logger = logging.getLogger(__name__)

@dataclass
class IdentifiedSong:
    song: str
    artist: str
    method: str
    spotify_track_id: str | None = None
    spotify_url: str | None = None
    added_to_playlist: bool = False
    error: str | None = None

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _is_duplicate(song1: IdentifiedSong, song2: IdentifiedSong, threshold: float = 0.8) -> bool:
    return (_similar(song1.song, song2.song) > threshold and
            _similar(song1.artist, song2.artist) > threshold)

def _deduplicate(songs: list[IdentifiedSong]) -> list[IdentifiedSong]:
    unique = []
    for song in songs:
        if not any(_is_duplicate(song, existing) for existing in unique):
            unique.append(song)
    return unique

async def identify_and_add(url: str) -> list[IdentifiedSong]:
    settings = get_settings()
    all_songs: list[IdentifiedSong] = []

    with tempfile.TemporaryDirectory(prefix="insta2spotify_") as work_dir:
        # Step 1: Get Instagram data (metadata + download)
        ig_data = await get_instagram_data(url, work_dir)

        # Method 1: Metadata
        if ig_data.track and ig_data.artist:
            all_songs.append(IdentifiedSong(
                song=ig_data.track,
                artist=ig_data.artist,
                method="metadata",
            ))
            logger.info("Metadata found: %s - %s", ig_data.artist, ig_data.track)

        # Method 2: OCR (if video available)
        if ig_data.video_path:
            try:
                ocr_results = await identify_songs_ocr(ig_data.video_path)
                for ocr in ocr_results:
                    all_songs.append(IdentifiedSong(
                        song=ocr.song,
                        artist=ocr.artist,
                        method="ocr",
                    ))
                    logger.info("OCR found: %s - %s", ocr.artist, ocr.song)
            except Exception as e:
                logger.warning("OCR failed: %s", e)

        # Method 3: Audio fingerprinting (if audio available)
        if ig_data.audio_path:
            try:
                shazam_results = await shazam_identify(
                    ig_data.audio_path,
                    segment_duration=settings.segment_duration,
                    overlap=settings.segment_overlap,
                )
                for sr in shazam_results:
                    all_songs.append(IdentifiedSong(
                        song=sr.song,
                        artist=sr.artist,
                        method="shazam",
                    ))
                    logger.info("Shazam found: %s - %s", sr.artist, sr.song)
            except Exception as e:
                logger.warning("Shazam failed: %s", e)

    # Deduplicate by fuzzy song+artist match
    unique_songs = _deduplicate(all_songs)

    # Search Spotify for all songs first
    for song in unique_songs:
        try:
            track = search_track(song.song, song.artist)
            if track:
                song.spotify_track_id = track["id"]
                song.spotify_url = track["url"]
            else:
                song.error = "Not found on Spotify"
        except Exception as e:
            song.error = str(e)
            logger.error("Spotify search error for %s - %s: %s", song.artist, song.song, e)

    # Deduplicate by Spotify track ID (catches cases like OCR "10 Avicii" vs Shazam "Avicii")
    seen_track_ids: set[str] = set()
    deduped: list[IdentifiedSong] = []
    for song in unique_songs:
        if song.spotify_track_id:
            if song.spotify_track_id in seen_track_ids:
                logger.info("Skipping duplicate Spotify track: %s - %s", song.artist, song.song)
                continue
            seen_track_ids.add(song.spotify_track_id)
        deduped.append(song)

    # Get existing playlist tracks once, then add new ones
    existing_ids = get_playlist_track_ids()
    for song in deduped:
        if song.spotify_track_id:
            try:
                song.added_to_playlist = add_to_playlist(song.spotify_track_id, existing_ids)
                existing_ids.add(song.spotify_track_id)
            except Exception as e:
                song.error = str(e)
                logger.error("Spotify add error for %s - %s: %s", song.artist, song.song, e)

    return deduped
