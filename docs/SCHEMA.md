# Database Schema

SQLite database. Created automatically on first startup.

## Tables

### users

Stores accounts. MVP has one hardcoded user; schema supports more.

```sql
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL
);
```

### boards

One board per user, stored as a JSON blob. MVP enforces this via application logic (one row per user seeded at startup).

```sql
CREATE TABLE IF NOT EXISTS boards (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    data    TEXT NOT NULL  -- JSON: BoardData
);
```

## BoardData JSON shape

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"] },
    { "id": "col-progress", "title": "In Progress", "cardIds": [] },
    { "id": "col-review", "title": "Review", "cardIds": [] },
    { "id": "col-done", "title": "Done", "cardIds": [] }
  ],
  "cards": {
    "card-1": { "id": "card-1", "title": "Example card", "details": "Card details." }
  }
}
```

## Notes

- Column order and card order within a column are encoded in `cardIds` arrays (ordered list).
- Column `id`s are fixed at seed time and never change. Only `title` is user-editable.
- The entire board is replaced on each `PUT /api/board` (no partial updates).
- The database file path is controlled via the `DB_PATH` environment variable (default: `kanban.db` in the working directory).
