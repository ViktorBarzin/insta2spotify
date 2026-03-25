import logging
import os
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from app.config import get_settings

logger = logging.getLogger(__name__)

def _get_oauth() -> SpotifyOAuth:
    settings = get_settings()
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope="playlist-modify-public playlist-modify-private",
        cache_path=settings.spotify_cache_path,
    )

def _seed_cache_from_refresh_token():
    """If cache file is empty/missing but we have a refresh token from Vault, seed the cache."""
    settings = get_settings()
    cache_path = Path(settings.spotify_cache_path)
    if cache_path.exists() and cache_path.stat().st_size > 10:
        return  # Cache already exists
    if not settings.spotify_refresh_token:
        return

    import json, time
    cache_data = {
        "access_token": "",
        "token_type": "Bearer",
        "expires_in": 0,
        "refresh_token": settings.spotify_refresh_token,
        "scope": "playlist-modify-public playlist-modify-private",
        "expires_at": int(time.time()) - 1,  # Force refresh on first use
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache_data))
    logger.info("Seeded Spotify cache from refresh token")

def get_spotify_client() -> spotipy.Spotify | None:
    _seed_cache_from_refresh_token()
    oauth = _get_oauth()
    token_info = oauth.get_cached_token()
    if not token_info:
        logger.warning("No Spotify token available. Visit /api/auth/login to authorize.")
        return None
    return spotipy.Spotify(auth=token_info["access_token"])

def get_auth_url() -> str:
    return _get_oauth().get_authorize_url()

def handle_callback(code: str) -> dict:
    return _get_oauth().get_access_token(code)

def search_track(song: str, artist: str) -> dict | None:
    sp = get_spotify_client()
    if not sp:
        return None
    query = f"track:{song} artist:{artist}"
    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    if not items:
        # Try broader search
        query = f"{song} {artist}"
        results = sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
    if items:
        track = items[0]
        return {
            "id": track["id"],
            "name": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "url": track["external_urls"].get("spotify"),
        }
    return None

def add_to_playlist(track_id: str) -> bool:
    settings = get_settings()
    sp = get_spotify_client()
    if not sp:
        return False
    try:
        # Check if already in playlist
        results = sp.playlist_tracks(settings.spotify_playlist_id)
        existing_ids = [item["track"]["id"] for item in results["items"] if item["track"]]
        if track_id in existing_ids:
            logger.info("Track %s already in playlist", track_id)
            return True
        sp.playlist_add_items(settings.spotify_playlist_id, [track_id])
        logger.info("Added track %s to playlist", track_id)
        return True
    except Exception as e:
        logger.error("Failed to add to playlist: %s", e)
        return False
