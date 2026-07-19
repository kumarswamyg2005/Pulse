# Pulse — How to run

Multi-tenant uptime-monitoring SaaS (React + FastAPI + Postgres + Celery + Redis).
Everything runs locally with Docker.

## Prerequisites

- Docker + Docker Compose
- Node 20+ (for the frontend dev server)

## 1. Start the backend

```bash
cp .env.example .env          # first time only
docker compose up -d --build  # starts db · redis · api · worker · beat
```

API is on **http://localhost:8000** (migrations run automatically).

## 2. Seed demo data

```bash
docker compose run --rm api python -m app.seed
```

## 3. Start the frontend

```bash
cd frontend
npm install                   # first time only
npm run dev
```

Open **http://localhost:5173**.

## Log in

The seed creates a demo team **"Demo Co"** (sample HTTP/TCP/ping monitors, an open incident,
and a public status page). Log in with any of these — password is `password123`:

| Email | Role | Can do |
|-------|------|--------|
| `owner@pulsedemo.com` | owner | everything, incl. billing |
| `admin@pulsedemo.com` | admin | monitors, members, incidents |
| `member@pulsedemo.com` | member | read-only + acknowledge incidents |

Or click **Sign up** to create your own team from scratch.

Public status page (no login): **http://localhost:5173/status/demo**

## Notes

- **Google sign-in** is hidden unless you set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` in
  `.env` (needs your own Google Cloud OAuth app). Email/password works without any setup.
- **Emails** (password reset, invites, alerts) print to the API logs in dev — view them with
  `docker compose logs -f api`.
- Monitors are checked on their interval by the background worker; status/uptime update live.

## Stop

```bash
docker compose down       # stop, keep data
docker compose down -v    # stop and wipe data
```
