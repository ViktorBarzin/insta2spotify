import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
import aiosqlite

from app.config import get_settings
from app.database import get_db, get_db_direct
from app.models import IdentifyRequest, SongResult
from app.services.identifier import identify_and_add

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_api_key(x_api_key: str = Header(...)):
    settings = get_settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

async def _process_request(request_id: int, url: str):
    """Background task to identify songs and add to Spotify."""
    db = await get_db_direct()
    try:
        songs = await identify_and_add(url)

        for song in songs:
            await db.execute(
                """INSERT INTO identifications
                   (request_id, song, artist, spotify_track_id, method, added_to_playlist, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (request_id, song.song, song.artist, song.spotify_track_id,
                 song.method, song.added_to_playlist, song.error),
            )

        status = "success" if any(s.added_to_playlist for s in songs) else "partial" if songs else "no_songs_found"
        await db.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
        await db.commit()
        logger.info("Request %d completed: %s (%d songs)", request_id, status, len(songs))
    except Exception as e:
        logger.exception("Identification failed for request %d: %s", request_id, url)
        await db.execute("UPDATE requests SET status = ? WHERE id = ?", ("error", request_id))
        await db.commit()
    finally:
        await db.close()

@router.post("/identify")
async def identify(
    request: IdentifyRequest,
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    cursor = await db.execute(
        "INSERT INTO requests (instagram_url, status) VALUES (?, ?)",
        (request.url, "processing"),
    )
    request_id = cursor.lastrowid
    await db.commit()

    background_tasks.add_task(_process_request, request_id, request.url)

    return {
        "status": "processing",
        "message": "Request accepted. Songs will be added to playlist in background.",
        "request_id": request_id,
    }
