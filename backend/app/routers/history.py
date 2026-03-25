from fastapi import APIRouter, Depends, Query
import aiosqlite

from app.database import get_db
from app.models import HistoryResponse, HistoryItem, SongResult

router = APIRouter()

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Get total count
    cursor = await db.execute("SELECT COUNT(*) FROM requests")
    row = await cursor.fetchone()
    total = row[0]

    # Get requests with their identifications
    cursor = await db.execute(
        "SELECT id, instagram_url, status, created_at FROM requests ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    requests = await cursor.fetchall()

    items = []
    for req in requests:
        cursor = await db.execute(
            "SELECT song, artist, method, spotify_track_id, added_to_playlist FROM identifications WHERE request_id = ?",
            (req[0],),
        )
        idents = await cursor.fetchall()
        songs = [
            SongResult(
                song=i[0] or "",
                artist=i[1] or "",
                method=i[2] or "",
                spotify_url=f"https://open.spotify.com/track/{i[3]}" if i[3] else None,
                added_to_playlist=bool(i[4]),
            )
            for i in idents
        ]
        items.append(HistoryItem(
            id=req[0],
            instagram_url=req[1],
            status=req[2],
            created_at=req[3],
            songs=songs,
        ))

    return HistoryResponse(items=items, total=total)
