from pydantic import BaseModel

class IdentifyRequest(BaseModel):
    url: str

class SongResult(BaseModel):
    song: str
    artist: str
    method: str
    spotify_url: str | None = None
    added_to_playlist: bool = False

class IdentifyResponse(BaseModel):
    status: str
    songs: list[SongResult]
    count: int
    request_id: int

class HistoryItem(BaseModel):
    id: int
    instagram_url: str
    status: str
    created_at: str
    songs: list[SongResult]

class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
