import sqlite3

DB_PATH = "grievances.db"


def get_connection():
    """Returns a new connection with rows accessible like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the tickets table if it doesn't already exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            name TEXT,
            contact TEXT,
            category TEXT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            resolution TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tickets)").fetchall()}
    if "details_json" not in columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN details_json TEXT")
    conn.close()


def generate_ticket_number(conn):
    """Generates sequential ticket numbers like TKT_00001, TKT_00002, ..."""
    row = conn.execute("SELECT COUNT(*) as count FROM tickets").fetchone()
    next_number = row["count"] + 1
    return f"TKT_{next_number:05d}"
