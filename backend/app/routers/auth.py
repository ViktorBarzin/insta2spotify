from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.services.spotify import get_auth_url, handle_callback

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login():
    return RedirectResponse(url=get_auth_url())

@router.get("/callback")
async def callback(code: str):
    handle_callback(code)
    return {"status": "ok", "message": "Spotify authorized successfully"}
