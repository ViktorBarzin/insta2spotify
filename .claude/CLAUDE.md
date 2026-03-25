# insta2spotify

## Project Overview
Identify songs in Instagram reels and add them to a Spotify playlist. Supports multi-song detection via metadata, OCR, and Shazam fingerprinting.

## Quick Start
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker-compose up
```

## Architecture
- **Backend**: FastAPI + aiosqlite + yt-dlp + shazamio + easyocr + spotipy
- **Frontend**: SvelteKit + Tailwind (history page only)
- **Auth**: API key for /api/identify (iOS Shortcut), Authentik for frontend
- **Song ID chain**: metadata (yt-dlp) + OCR (easyocr) + audio fingerprint (shazamio) → merge & deduplicate → Spotify search → add to playlist

## Key Files
- `backend/app/services/identifier.py` — orchestrator: runs all 3 methods, deduplicates, adds to Spotify
- `backend/app/services/fingerprint.py` — shazamio with audio segment splitting
- `backend/app/services/spotify.py` — OAuth flow + playlist management
- `backend/app/routers/identify.py` — main POST endpoint with API key auth

## Environment Variables
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` — Spotify OAuth app credentials
- `SPOTIFY_REDIRECT_URI` — OAuth callback URL
- `SPOTIFY_PLAYLIST_ID` — Target playlist (default: 7lcLakPy8pwwegFoOQ7MoG)
- `SPOTIFY_REFRESH_TOKEN` — Seeded from Vault on first deploy
- `API_KEY` — Required for POST /api/identify
- `DATABASE_PATH` — SQLite path (default: /data/insta2spotify.db)

## Deployment
- Namespace: `insta2spotify`, tier: 4-aux
- Two containers in one pod (frontend:3000, backend:8000)
- NFS volume at /data for SQLite + Spotify cache
- Split ingress: frontend protected (Authentik), /api/identify unprotected (API key auth)
- Initial Spotify OAuth: visit https://insta2spotify.viktorbarzin.me/api/auth/login
