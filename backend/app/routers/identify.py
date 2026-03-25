import logging

from fastapi import APIRouter, Depends, Header, HTTPException
import aiosqlite

from app.config import get_settings
from app.database import get_db
from app.models import IdentifyRequest, IdentifyResponse, SongResult
from app.services.identifier import identify_and_add

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_api_key(x_api_key: str = Header(...)):
    settings = get_settings()
    if not settings.api_key:
        return  # No key configured, allow all
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.post("/identify", response_model=IdentifyResponse)
async def identify(
    request: IdentifyRequest,
    db: aiosqlite.Connection = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    # Create request record
    cursor = await db.execute(
        "INSERT INTO requests (instagram_url, status) VALUES (?, ?)",
        (request.url, "processing"),
    )
    request_id = cursor.lastrowid
    await db.commit()

    try:
        songs = await identify_and_add(request.url)

        # Save identifications
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

        return IdentifyResponse(
            status=status,
            songs=[SongResult(
                song=s.song, artist=s.artist, method=s.method,
                spotify_url=s.spotify_url, added_to_playlist=s.added_to_playlist,
            ) for s in songs],
            count=len(songs),
            request_id=request_id,
        )
    except Exception as e:
        logger.exception("Identification failed for %s", request.url)
        await db.execute("UPDATE requests SET status = ? WHERE id = ?", ("error", request_id))
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))
