from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Runtime connection: non-superuser role, so Postgres RLS is actually enforced.
    database_url: str = "postgresql+psycopg://pulse_app:pulse_app@localhost:5432/pulse"
    # Admin/superuser connection: migrations, role creation, RLS setup.
    admin_database_url: str = "postgresql+psycopg://pulse:pulse@localhost:5432/pulse"
    app_role_password: str = "pulse_app"

    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    log_format: str = "json"  # "json" | "console"
    sentry_dsn: str | None = None

    frontend_origin: str = "http://localhost:5173"
    session_cookie_name: str = "pulse_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 14  # 14 days
    session_secret: str = "dev-secret-change-me"  # signs the OAuth-state cookie

    # Email (Resend in prod; console outbox in dev/test)
    resend_api_key: str | None = None
    email_from: str = "Pulse <onboarding@resend.dev>"
    password_reset_ttl_seconds: int = 60 * 60  # 1 hour
    invite_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days

    # Incident state machine
    incident_open_threshold: int = 3  # consecutive failures before opening
    incident_resolve_threshold: int = 2  # consecutive successes before resolving
    cert_warning_days: int = 14  # warn when a TLS cert expires within this many days

    # Google OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str = "whsec_test"
    stripe_price_pro: str | None = None
    stripe_price_team: str | None = None
    billing_success_url: str = "http://localhost:5173/billing?success=1"
    billing_cancel_url: str = "http://localhost:5173/billing?canceled=1"

    def tier_for_price(self, price_id: str | None) -> str | None:
        if price_id and price_id == self.stripe_price_pro:
            return "pro"
        if price_id and price_id == self.stripe_price_team:
            return "team"
        return None

    def price_for_tier(self, tier: str) -> str | None:
        return {"pro": self.stripe_price_pro, "team": self.stripe_price_team}.get(tier)

    @property
    def email_backend(self) -> str:
        return "resend" if self.resend_api_key else "console"

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_samesite(self) -> Literal["lax", "none"]:
        # cross-origin (Vercel <-> Railway) needs None+Secure in prod; Lax is fine on localhost.
        return "none" if self.environment == "production" else "lax"


settings = Settings()
