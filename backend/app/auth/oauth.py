from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts import get_or_create_oauth_user
from app.auth.routes import set_session_cookie
from app.config import settings
from app.deps import get_db
from app.sessions import create_session

router = APIRouter(prefix="/auth/google", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login")
async def google_login(request: Request):
    if not settings.google_client_id:
        raise HTTPException(503, "Google OAuth not configured")
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(400, "Google did not return an email")
    user, team_id = await get_or_create_oauth_user(db, userinfo["email"])
    session_token = await create_session(user.id, team_id)
    response = RedirectResponse(url=settings.frontend_origin)
    set_session_cookie(response, session_token)
    return response
