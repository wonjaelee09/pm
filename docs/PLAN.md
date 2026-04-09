# Project Management MVP — Detailed Execution Plan

## Part 1: Plan (this document)

**Goal**: Produce a detailed, checkable plan and document the existing frontend codebase.

### Substeps
- [ ] Replace docs/PLAN.md with detailed version (this document)
- [ ] Create frontend/AGENTS.md documenting the existing frontend code

### Success criteria
- docs/PLAN.md exists with all 10 parts expanded
- frontend/AGENTS.md exists and accurately describes the existing code
- No code has been changed

---

## Part 2: Scaffolding

**Goal**: Stand up the Docker container with FastAPI serving a hello-world static page and a working API endpoint.

### Substeps
- [ ] Create `backend/` Python project with `uv` (`pyproject.toml`, `uv.lock`)
- [ ] Add FastAPI and uvicorn as dependencies via uv
- [ ] Create `backend/main.py` with:
  - A `GET /api/health` route returning `{"status": "ok"}`
  - Static file mounting to serve `frontend/out/` at `/`
  - Fallback to a placeholder `index.html` for now
- [ ] Create `Dockerfile` at project root:
  - Build stage: install Node, build frontend (`npm ci && npm run build`)
  - Runtime stage: install uv + Python deps, copy built frontend into container, run uvicorn
- [ ] Create `scripts/start.sh` (Mac/Linux) and `scripts/start.bat` + `scripts/start.ps1` (Windows):
  - Build Docker image
  - Run container, mapping port 8000, mounting `.env` for secrets
- [ ] Create `scripts/stop.sh`, `scripts/stop.bat`, `scripts/stop.ps1`:
  - Stop and remove the running container
- [ ] Verify hello-world HTML is served at `http://localhost:8000/`
- [ ] Verify `GET /api/health` returns `{"status": "ok"}`

### Tests / verification
- `curl http://localhost:8000/` returns 200 with HTML
- `curl http://localhost:8000/api/health` returns `{"status": "ok"}`

### Success criteria
- Docker container builds and runs from a single script invocation
- Both routes respond correctly
- No frontend changes required yet

---

## Part 3: Add Frontend

**Goal**: The Next.js frontend is statically built inside Docker and served at `/`.

### Substeps
- [ ] Add `output: 'export'` to `frontend/next.config.ts` for static export
- [ ] Confirm `npm run build` produces `frontend/out/` with static HTML/JS/CSS
- [ ] Update Dockerfile build stage to copy `frontend/out/` into the image
- [ ] Update `backend/main.py` to mount `frontend/out/` as static files at `/`
- [ ] Add a catch-all route in FastAPI to serve `index.html` for client-side routing
- [ ] Rebuild Docker image and verify the Kanban board loads at `http://localhost:8000/`
- [ ] Run existing frontend unit tests (`npm run test:unit`) — all must pass
- [ ] Run existing E2E tests against the Docker-served app (`npm run test:e2e`) — all must pass

### Tests / verification
- `npm run test:unit` passes (Vitest)
- `npm run test:e2e` passes against `http://localhost:8000` (Playwright)
- Manual: Kanban board visible with all 5 columns and sample cards

### Success criteria
- Full frontend renders correctly when served from FastAPI/Docker
- All existing tests pass unchanged

---

## Part 4: Fake Sign-In

**Goal**: Users must log in with hardcoded credentials (`user` / `password`) before seeing the Kanban board; logout is available.

### Substeps
- [ ] Add a `POST /api/auth/login` route to FastAPI:
  - Accepts `{ username, password }` JSON
  - Returns `{ ok: true }` + sets an HTTP-only session cookie on success
  - Returns 401 on failure
- [ ] Add a `POST /api/auth/logout` route:
  - Clears the session cookie
- [ ] Add a `GET /api/auth/me` route:
  - Returns `{ username }` if logged in, 401 if not
- [ ] Add a `/login` page to the Next.js frontend:
  - Simple form: username + password fields + submit button
  - On success, redirect to `/`
  - On failure, show an error message
- [ ] Update root page (`/`) to check auth on load; redirect to `/login` if not authenticated
- [ ] Add a logout button to the Kanban board header
- [ ] Update `frontend/next.config.ts` `output: 'export'` approach — since auth requires API calls, confirm SPA routing works with the FastAPI catch-all
- [ ] Write backend unit tests (pytest) for login/logout/me routes
- [ ] Write frontend component tests for the login form (Vitest)
- [ ] Write E2E test: unauthenticated user sees login page, logs in, sees board, logs out

### Tests / verification
- `pytest backend/` — login/logout/me tests pass
- `npm run test:unit` — login form tests pass
- `npm run test:e2e` — full auth flow E2E passes

### Success criteria
- Unauthenticated requests to `/` redirect to `/login`
- Correct credentials grant access; incorrect credentials show error
- Logout clears session and redirects to `/login`

---

## Part 5: Database Modeling

**Goal**: Design and document the SQLite schema for the Kanban board; get user approval before any backend code is written.

### Substeps
- [ ] Design schema supporting:
  - Multiple users (for future expansion)
  - One board per user (MVP)
  - Fixed columns (renameable)
  - Cards with title, details, position within column
- [ ] Save schema as `docs/SCHEMA.md` with:
  - Entity descriptions
  - SQL `CREATE TABLE` statements
  - Example JSON representation of a board
  - Notes on ordering (explicit `position` integer vs. ordered list)
- [ ] **STOP — present schema to user and wait for approval before continuing to Part 6**

### Tests / verification
- docs/SCHEMA.md exists and is complete
- User has explicitly approved the schema

### Success criteria
- Schema doc written and approved
- No database code written yet

---

## Part 6: Backend API

**Goal**: Implement API routes for reading and mutating the Kanban board, backed by SQLite.

### Substeps
- [ ] Create `backend/database.py`:
  - `init_db()` creates tables if they don't exist (run on startup)
  - Helper functions: `get_board(user_id)`, `save_board(user_id, board_data)`
  - Seed the hardcoded user's board with `initialData` equivalent on first run
- [ ] Add API routes to `backend/main.py`:
  - `GET /api/board` — returns full board JSON for authenticated user
  - `PUT /api/board` — replaces full board JSON for authenticated user
- [ ] All routes require valid session cookie (401 if missing)
- [ ] Write pytest unit tests for:
  - `init_db()` creates correct schema
  - `GET /api/board` returns expected data
  - `PUT /api/board` persists changes
  - Unauthenticated requests return 401

### Tests / verification
- `pytest backend/` — all tests pass
- Manual: `curl` with valid session cookie returns board JSON

### Success criteria
- SQLite DB is created automatically on first run
- Board data persists across container restarts (volume mount)
- All API routes return correct status codes and data

---

## Part 7: Frontend + Backend Integration

**Goal**: The frontend reads from and writes to the backend API; the app is a fully persistent Kanban board.

### Substeps
- [ ] Replace `initialData` usage in `KanbanBoard.tsx` with a `GET /api/board` fetch on mount
- [ ] After every board mutation (drag-drop, rename column, add card, delete card), call `PUT /api/board` with the updated board JSON
- [ ] Handle loading and error states (simple spinner / error message)
- [ ] Update `KanbanBoard.test.tsx` to mock API calls
- [ ] Write new integration tests (Vitest) covering:
  - Board loads from API on mount
  - Card move triggers PUT request
  - Column rename triggers PUT request
  - Add/delete card triggers PUT request
- [ ] Update E2E tests to run against full Docker stack:
  - Login → see board → move card → reload page → card is still in new column

### Tests / verification
- `npm run test:unit` — all unit + integration tests pass
- `npm run test:e2e` — full persistent board E2E passes
- Manual: card moved in browser persists after page refresh

### Success criteria
- All state changes are persisted to the database
- No stale in-memory state; source of truth is the API
- Tests cover all mutation paths

---

## Part 8: AI Connectivity

**Goal**: Confirm the backend can successfully make an AI call via OpenRouter.

### Substeps
- [ ] Add `openai` Python package (OpenAI-compatible client) as a dependency via uv
- [ ] Create `backend/ai.py` with an `ask(prompt: str) -> str` function:
  - Uses `openai` client pointed at OpenRouter base URL
  - Uses `OPENROUTER_API_KEY` from environment
  - Model: `openai/gpt-oss-120b`
- [ ] Add a `POST /api/ai/test` route (dev only) that calls `ask("What is 2+2?")` and returns the response
- [ ] Write a pytest test that calls `ask("What is 2+2?")` and asserts the response contains "4" (requires live API key; skip in CI if key absent)
- [ ] Verify manually that the route returns a sensible response

### Tests / verification
- `pytest backend/tests/test_ai.py` passes (with API key in env)
- Manual: `POST /api/ai/test` returns `{"response": "...4..."}` or similar

### Success criteria
- AI call succeeds end-to-end from inside the Docker container
- OPENROUTER_API_KEY is read from `.env` and never hardcoded

---

## Part 9: Extended AI Integration

**Goal**: The AI receives the full board JSON + conversation history and responds with structured output that may include board mutations.

### Substeps
- [ ] Define a Pydantic response model in `backend/ai.py`:
  ```
  class AIResponse(BaseModel):
      message: str               # reply shown to user
      board_update: BoardData | None  # optional full board replacement
  ```
- [ ] Update `ask()` to accept `board_json`, `user_message`, `history` params
- [ ] Craft a system prompt that:
  - Describes the board structure (JSON schema)
  - Instructs the AI to return structured output
  - Lists available actions (move card, rename column, add card, delete card)
- [ ] Use OpenAI `response_format` with JSON schema to enforce structured output
- [ ] Add `POST /api/ai/chat` route:
  - Requires auth
  - Accepts `{ message: str, history: [...] }`
  - Fetches current board, calls AI, optionally saves updated board
  - Returns `{ message: str, board_updated: bool }`
- [ ] Write pytest tests for:
  - Correct system prompt construction
  - Parsing a mocked AI response with and without board_update
  - `POST /api/ai/chat` end-to-end with mocked AI (no live calls in unit tests)

### Tests / verification
- `pytest backend/` passes with mocked AI
- Manual: send a chat message like "move card X to Done" and verify board updates

### Success criteria
- AI correctly receives board context and history
- Board is updated when AI returns a `board_update`
- No board change when AI returns `board_update: null`

---

## Part 10: AI Chat Sidebar

**Goal**: A polished chat sidebar in the UI enables full AI conversation; board auto-refreshes when the AI makes changes.

### Substeps
- [ ] Create `src/components/ChatSidebar.tsx` (client component):
  - Input field + send button at bottom
  - Message history displayed above (user and AI messages)
  - Loading indicator while waiting for AI
  - Styled using project color scheme (purple submit button, navy headings, etc.)
- [ ] Add sidebar toggle button to `KanbanBoard.tsx` header
- [ ] When `POST /api/ai/chat` returns `board_updated: true`, re-fetch the board via `GET /api/board` and update state
- [ ] Conversation history is kept in component state and sent with each message
- [ ] Write Vitest tests for `ChatSidebar`:
  - Renders input and empty history
  - Submitting a message shows user message immediately
  - AI response appears after fetch resolves
  - Board refresh is triggered when `board_updated: true`
- [ ] Update E2E test:
  - Open sidebar, type a message, verify AI response appears
  - Type a board mutation command, verify the board updates visually

### Tests / verification
- `npm run test:unit` — ChatSidebar tests pass
- `npm run test:e2e` — AI chat E2E test passes
- Manual: full conversation flow with live AI, including board mutations

### Success criteria
- Chat sidebar is visually polished and matches the design system
- Board refreshes automatically after AI mutations — no manual reload needed
- Conversation history is preserved within a session
