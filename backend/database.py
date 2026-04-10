import json
import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "kanban.db")

# M7: must stay in sync with initialData in frontend/src/lib/kanban.ts (used as test fixture)
INITIAL_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {"id": "card-1", "title": "Align roadmap themes", "details": "Draft quarterly themes with impact statements and metrics."},
        "card-2": {"id": "card-2", "title": "Gather customer signals", "details": "Review support tags, sales notes, and churn feedback."},
        "card-3": {"id": "card-3", "title": "Prototype analytics view", "details": "Sketch initial dashboard layout and key drill-downs."},
        "card-4": {"id": "card-4", "title": "Refine status language", "details": "Standardize column labels and tone across the board."},
        "card-5": {"id": "card-5", "title": "Design card layout", "details": "Add hierarchy and spacing for scanning dense lists."},
        "card-6": {"id": "card-6", "title": "QA micro-interactions", "details": "Verify hover, focus, and loading states."},
        "card-7": {"id": "card-7", "title": "Ship marketing page", "details": "Final copy approved and asset pack delivered."},
        "card-8": {"id": "card-8", "title": "Close onboarding sprint", "details": "Document release notes and share internally."},
    },
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = _connect()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                data TEXT NOT NULL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", ("user",))
        row = conn.execute("SELECT id FROM users WHERE username = ?", ("user",)).fetchone()
        user_id = row["id"]
        existing = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO boards (user_id, data) VALUES (?, ?)",
                (user_id, json.dumps(INITIAL_BOARD)),
            )
    conn.close()


def get_board(username: str) -> dict:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT b.data FROM boards b JOIN users u ON b.user_id = u.id WHERE u.username = ?",
            (username,),
        ).fetchone()
        if not row:
            raise ValueError(f"No board found for user: {username}")
        return json.loads(row["data"])
    finally:
        conn.close()


def save_board(username: str, board_data: dict) -> None:
    conn = _connect()
    with conn:
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError(f"User not found: {username}")
        conn.execute(
            "UPDATE boards SET data = ? WHERE user_id = ?",
            (json.dumps(board_data), row["id"]),
        )
    conn.close()
