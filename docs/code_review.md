# Code Review

Reviewed 2026-04-09. All findings verified against source.

---

## Summary

| Severity | Count |
|---|---|
| High | 2 |
| Medium | 7 |
| Low | 6 |

---

## High

### H1 — `saveBoard()` is fire-and-forget with no error handling
**File:** `frontend/src/components/KanbanBoard.tsx:26-32`

`saveBoard()` fires a `PUT /api/board` request and returns `void` with no `.catch()`, no `await`, and no error state. If the request fails, the board drifts silently: the user sees their changes locally but they are not persisted. All four mutation handlers (`handleDragEnd`, `handleRenameColumn`, `handleAddCard`, `handleDeleteCard`) call this.

**Fix:** At minimum, log the failure and surface an error banner. Proper fix: make `saveBoard` async, `await` it in each handler, and set an error state on failure.

---

### H2 — `SECRET_KEY` silently falls back to a weak default
**File:** `backend/main.py:13`

```python
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
```

If `SECRET_KEY` is absent from the environment, Starlette's session middleware signs cookies with `"dev-secret-key"`. Anyone who knows the default can forge session cookies.

**Fix:** Fail loudly at startup when the key is missing:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
```

---

## Medium

### M1 — `/api/ai/test` endpoint is unauthenticated
**File:** `backend/main.py:94-97`

The `/api/ai/test` route calls the live OpenRouter API but has no `_require_auth()` check. Any unauthenticated caller can trigger API spend.

**Fix:** Add `_require_auth(request)` or remove the route if it was only needed for development verification.

---

### M2 — `PUT /api/board` accepts any JSON without schema validation
**File:** `backend/main.py:80-84`

```python
async def put_board(request: Request):
    data = await request.json()
    database.save_board(user, data)
```

`request.json()` accepts arbitrary JSON. A malformed payload (wrong shape, missing fields) is written directly to the database and will break `GET /api/board` for that user.

**Fix:** Define a Pydantic model matching `BoardData` and use it as the request body parameter so FastAPI validates before the handler runs.

---

### M3 — `ChatRequest.history` is untyped
**File:** `backend/main.py:89-91`

```python
class ChatRequest(BaseModel):
    history: list[dict] = []
```

Unvalidated `dict` entries are forwarded directly to the OpenAI client. An invalid message structure (e.g., unknown `role`) will cause a 500 from OpenRouter rather than a clean 422.

**Fix:**
```python
from typing import Literal
class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []
```

---

### M4 — `refreshBoard()` has no error handling
**File:** `frontend/src/components/KanbanBoard.tsx:53-56`

```typescript
const refreshBoard = async () => {
  const updated = await fetchBoard();  // can throw
  setBoard(updated);
};
```

Called by `ChatSidebar` after a board-mutating AI response. If the fetch fails, the uncaught exception propagates to `ChatSidebar`'s catch block which shows a generic "something went wrong" message — even though the AI actually succeeded.

**Fix:** Wrap in try/catch and set an appropriate error state.

---

### M5 — Static file serving has no path traversal guard
**File:** `backend/main.py:112-120`

```python
candidate = os.path.join(STATIC_DIR, full_path)
if os.path.isfile(candidate):
    return FileResponse(candidate)
```

No check that the resolved path stays within `STATIC_DIR`. While FastAPI's path parameter sanitizes many cases, it is not guaranteed to block all traversal sequences.

**Fix:**
```python
real_static = os.path.realpath(STATIC_DIR)
candidate = os.path.realpath(os.path.join(STATIC_DIR, full_path))
if not candidate.startswith(real_static + os.sep):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
```

---

### M6 — SessionMiddleware missing `https_only=True`
**File:** `backend/main.py:25`

```python
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
```

Starlette's default is `https_only=False`, meaning the session cookie is sent over plain HTTP. For a local-only MVP this is acceptable, but should be noted as a pre-deployment requirement.

**Fix:** Set `https_only=True` when deploying behind HTTPS, or make it configurable via env var.

---

### M7 — Duplicate initial board data
**Files:** `frontend/src/lib/kanban.ts` (`initialData`), `backend/database.py` (`INITIAL_BOARD`)

Both define the same 5-column, 8-card board independently. They are currently in sync but will drift as either side evolves. Tests that use `initialData` from the frontend will pass even if the backend seeds different data.

**Fix:** The frontend's `initialData` is only used as a prop default in `ChatSidebar.test.tsx`. Remove it from production code — the board always comes from `GET /api/board`. In tests, build the expected board from a shared fixture or fetch it from the test client.

---

## Low

### L1 — `mockFetch` declared but never used in `ChatSidebar.test.tsx`
**File:** `frontend/src/components/ChatSidebar.test.tsx:15`

```typescript
const mockFetch = vi.fn;  // missing (), never referenced
```

`vi.fn` (without `()`) is just the function factory itself, not a mock instance. The variable is never used; the actual stub is set up in `beforeEach`. Dead code.

**Fix:** Delete the line.

---

### L2 — No `VOLUME` instruction in Dockerfile
**File:** `Dockerfile`

The database is stored at `/app/data/kanban.db`. The `start.sh` script correctly mounts a host volume there, but the Dockerfile has no `VOLUME /app/data` declaration. Without it, Docker doesn't signal that this path needs external persistence, which could surprise anyone running the image directly.

**Fix:** Add `VOLUME /app/data` before the `EXPOSE` line.

---

### L3 — No `HEALTHCHECK` in Dockerfile
**File:** `Dockerfile`

Docker has no way to detect if the application is up and serving requests.

**Fix:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
```

---

### L4 — No `.env.example`
**Project root**

The required environment variables (`OPENROUTER_API_KEY`, `SECRET_KEY`, `DB_PATH`) are not documented anywhere except indirectly in `start.sh`. A new developer has no template to work from.

**Fix:** Add a `.env.example` with placeholder values and a brief comment for each variable.

---

### L5 — No test for `GET /api/health`
**File:** `backend/tests/` (missing)

The health endpoint is used as a Docker HEALTHCHECK target (once L3 is fixed) but has no test. Trivial to add.

---

### L6 — `saveBoard()` called with stale board state on rapid edits
**File:** `frontend/src/components/KanbanBoard.tsx`

React state updates are synchronous within a handler, but `saveBoard()` is fire-and-forget. If a user performs two mutations in quick succession (e.g., add a card and immediately rename a column), both `saveBoard()` calls are in flight with the state at the time of each call. The second PUT will win, but if requests arrive out of order, the first could overwrite the second. For a single-user local app the risk is low, but it is worth noting as a last-write-wins race.

**Fix:** Serialize saves (queue or debounce), or use an optimistic update pattern with rollback on failure.
