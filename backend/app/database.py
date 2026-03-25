import aiosqlite
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instagram_url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER REFERENCES requests(id),
    song TEXT,
    artist TEXT,
    spotify_track_id TEXT,
    method TEXT,
    added_to_playlist BOOLEAN DEFAULT 0,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def init_db():
    settings = get_settings()
    async with aiosqlite.connect(settings.database_path) as db:
        await db.executescript(_DB_SCHEMA)
        await db.commit()
    logger.info("Database initialized at %s", settings.database_path)

async def get_db():
    settings = get_settings()
    db = await aiosqlite.connect(settings.database_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def get_db_direct() -> aiosqlite.Connection:
    """Non-generator version for background tasks."""
    settings = get_settings()
    db = await aiosqlite.connect(settings.database_path)
    db.row_factory = aiosqlite.Row
    return db
