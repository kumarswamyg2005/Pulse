import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth.oauth import router as oauth_router
from app.auth.routes import router as auth_router
from app.billing.routes import router as billing_router
from app.config import settings
from app.health import router as health_router
from app.incidents.routes import router as incidents_router
from app.logging import RequestIdMiddleware, configure_logging
from app.monitors.routes import router as monitors_router
from app.ratelimit import limiter
from app.status.routes import router as status_router
from app.teams.routes import router as teams_router
from app.webhooks.routes import router as webhooks_router

configure_logging(settings.log_level, settings.log_format)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(title="Pulse API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIdMiddleware)
# Signed cookie for the OAuth state handshake (Authlib stores state here).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.cookie_secure,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(teams_router)
app.include_router(monitors_router)
app.include_router(incidents_router)
app.include_router(webhooks_router)
app.include_router(billing_router)
app.include_router(status_router)
