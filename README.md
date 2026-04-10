# Kanban Studio

A single-board Kanban app with drag-and-drop, column renaming, and an AI chat sidebar. Runs locally in Docker.

## Features

- Drag cards between columns
- Rename columns inline
- Add and delete cards
- AI assistant that can move, add, and rename cards via chat
- Session-based authentication (single hardcoded user)

## Quick Start

**Requirements:** Docker

1. Copy the example env file and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENROUTER_API_KEY and SECRET_KEY
   ```

2. Start the app:
   ```bash
   ./scripts/start.sh        # Mac / Linux
   scripts\start.bat         # Windows (cmd)
   scripts\start.ps1         # Windows (PowerShell)
   ```

3. Open [http://localhost:8000](http://localhost:8000) and sign in with `user` / `password`.

4. To stop:
   ```bash
   ./scripts/stop.sh
   ```

Board data is persisted in `./data/kanban.db` on your machine.

## Development

**Frontend** (Next.js, runs on port 3000):
```bash
cd frontend
npm install
npm run dev
```

**Backend** (FastAPI, runs on port 8000):
```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Tests:**
```bash
# Frontend
cd frontend
npm run test:unit   # Vitest unit tests
npm run test:e2e    # Playwright E2E tests

# Backend
cd backend
uv run pytest
```

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| Drag and drop | dnd-kit |
| Backend | FastAPI, SQLite |
| AI | OpenRouter (`openai/gpt-oss-120b`) |
| Runtime | Docker (multi-stage build) |
