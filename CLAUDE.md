# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Project Management MVP: a single-board Kanban app with drag-and-drop, column renaming, and an AI chat sidebar. One user (hardcoded `user`/`password`), one board, runs locally in Docker. AI calls go through OpenRouter using model `openai/gpt-oss-120b`. The `OPENROUTER_API_KEY` is in `.env` at the project root.

**Read `docs/PLAN.md` before working on new features.** It contains the 10-part execution plan and tracks what has been completed.

## Architecture

```
frontend/   Next.js 16 static export (output: 'export' → out/)
backend/    FastAPI — serves frontend static files at / and REST API at /api/*
Dockerfile  Multi-stage: Node build → Python runtime
scripts/    start/stop for Mac, Linux, Windows (wraps docker build + run)
```

The backend serves the compiled frontend from `backend/static/` (copied from `frontend/out/` during Docker build). In development, frontend and backend run separately.

**Data model** (`src/lib/kanban.ts`):
- `BoardData = { columns: Column[], cards: Record<string, Card> }`
- `Column = { id, title, cardIds: string[] }` — ordered list of card IDs
- `Card = { id, title, details }`
- `moveCard(board, activeId, overId)` handles same-column reorder and cross-column moves

**State**: All board state lives in `KanbanBoard` (no Context/Redux). Children receive data + callbacks via props.

**API routes** (all implemented):
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — session cookie auth
- `GET /api/board`, `PUT /api/board` — full board JSON read/replace (auth required)
- `POST /api/ai/chat` — accepts `{ message, history }`, returns `{ message, board_updated }` (auth required)
- `POST /api/ai/test` — dev-only smoke test for OpenRouter connectivity
- `GET /api/health` — returns `{"status": "ok"}`

## Commands

### Frontend (run from `frontend/`)
```bash
npm run dev              # Dev server on port 3000
npm run build            # Static export to out/
npm run lint             # ESLint
npm run test:unit        # Vitest (once)
npm run test:unit:watch  # Vitest watch
npm run test:e2e         # Playwright E2E (starts dev server automatically)
npm run test:all         # Unit + E2E
```

Run a single Vitest test file:
```bash
npx vitest run src/lib/kanban.test.ts
```

Run a single Playwright test:
```bash
npx playwright test tests/kanban.spec.ts --grep "adds a card"
```

### Backend (run from `backend/`)
```bash
uv sync                                                        # Install deps
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload   # Dev server
uv run pytest                                                  # Run all backend tests
uv run pytest tests/test_auth.py                               # Run a single test file
```

### Docker
```bash
./scripts/start.sh   # Build image + run container on port 8000
./scripts/stop.sh    # Stop + remove container
```

## Coding Standards

1. Use latest versions of libraries and idiomatic approaches.
2. **Keep it simple** — never over-engineer, no unnecessary defensive programming, no extra features.
3. No emojis, ever.
4. When hitting issues, identify root cause with evidence before fixing. Do not guess.

## Design Tokens

CSS custom properties defined in `frontend/src/app/globals.css` (Tailwind v4, no `tailwind.config.js`):

| Token | Value | Use |
|---|---|---|
| `--accent-yellow` | `#ecad0a` | Highlights, column indicators |
| `--primary-blue` | `#209dd7` | Links, borders, focus rings |
| `--secondary-purple` | `#753991` | Submit buttons, key actions |
| `--navy-dark` | `#032147` | Main headings |
| `--gray-text` | `#888888` | Labels, supporting text |

## Testing

- Unit + component tests: Vitest with jsdom, files colocated as `*.test.ts(x)`
- E2E: Playwright, Chromium only, `baseURL: http://127.0.0.1:3000`
- Playwright auto-starts `next dev` via `webServer` config — no need to start it manually
