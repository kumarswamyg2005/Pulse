# 03 — Google OAuth + password reset + email sender

**What to build:** Google OAuth login/link via Authlib. A small email sender wrapper (Resend in prod, console/file backend in dev, config-switched). Password reset via a signed, expiring emailed token. Frontend "Continue with Google" button and forgot/reset-password flow.

**Blocked by:** 02

**Status:** done

- [x] Google OAuth endpoints wired via Authlib (login redirect + callback upsert); `get_or_create_oauth_user` unit-tested; live-Google flow needs real creds (returns 503 until configured)
- [x] Forgot-password sends a tokenized email (captured in tests; logged to console in dev)
- [x] Reset with a valid token sets a new password; expired/used tokens rejected; single-use
- [x] Email sender: console outbox in dev/test, Resend API in prod (auto-switch on RESEND_API_KEY)

## Comments

Backend green: ruff + mypy + 14 pytest. Verified live in Docker: forgot→202 + reset link in logs, reset flow tested end-to-end, `google/login`→503 without creds. Frontend adds "Continue with Google" + forgot/reset pages; build green. Fixed: httpx moved dev→main (Authlib + Resend need it at runtime, `--no-dev` image was crashing).
