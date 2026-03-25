from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Spotify
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    spotify_playlist_id: str = "7lcLakPy8pwwegFoOQ7MoG"
    spotify_cache_path: str = "/data/.spotify_cache"
    spotify_refresh_token: str = ""

    # API auth
    api_key: str = ""

    # Database
    database_path: str = "/data/insta2spotify.db"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Instagram
    instagram_cookies_path: str = "/data/instagram_cookies.txt"

    # Audio processing
    segment_duration: int = 15  # seconds per Shazam chunk
    segment_overlap: int = 5   # overlap between chunks

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

@lru_cache
def get_settings() -> Settings:
    return Settings()
