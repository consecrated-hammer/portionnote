# Portion Note Technical Guide

This document covers setup, configuration, and operational details for running Portion Note.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

App: http://localhost:8001
API health: http://localhost:8001/api/health
API docs: http://localhost:8001/docs

## Configuration

All settings are in `.env`. Start from `.env.example`.

Required:

```bash
ADMIN_EMAIL=admin@portionnote.local
ADMIN_PASSWORD=change-me
INVITE_CODE=invite-me
SESSION_SECRET=change-me
```

Common optional settings:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
SCRAPER_API_KEY=
```

## Authentication notes

- Local email and password login is supported.
- Google sign in is optional and invite gated.
- Admin accounts can create invite links in Settings.

## Logging

- Backend logs to `LOG_DIR/LOG_FILE_NAME` with rotation via `LOG_MAX_BYTES` and `LOG_BACKUP_COUNT`.
- Set `LOG_LEVEL`, `LOG_CONSOLE_LEVEL`, and `LOG_FILE_LEVEL` to control verbosity.
- Frontend logs are batched to `POST /api/logs/batch` and written to the same file.
- Use `LOG_FRONTEND_RATE_LIMIT_PER_MIN` to limit log intake from browsers.

## Food lookup sources

Portion Note can enrich food search using these sources:

- OpenFoodFacts (primary)
- Coles and Woolworths via ScraperAPI (optional)
- AI fallback for unmatched items

To enable scraping, set `SCRAPER_API_KEY`. AI fallback uses `OPENAI_API_KEY`.

## Development

Backend (without Docker):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:App --reload --port 8001
```

Frontend (without Docker):

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
./scripts/backend.sh test
./scripts/frontend.sh test
```

## Deployment

Traefik production:

```bash
docker network create traefik_proxy
docker compose -f docker-compose.traefik.yml up -d --build
```

Traefik dev domain:

```bash
docker compose --env-file .env.dev -f docker-compose.traefik.dev.yml up -d --build
```

## Troubleshooting

View logs:

```bash
docker compose logs -f app
```

Reset database:

```bash
docker compose down
docker volume rm portionnote-data
docker compose up --build
```
