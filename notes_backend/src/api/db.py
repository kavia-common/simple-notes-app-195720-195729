import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SqliteConfig:
    """Configuration for SQLite access."""

    db_path: str


def _repo_root_from_this_file() -> Path:
    """
    Locate the mono-repo root from this file location.

    notes_backend/src/api/db.py -> go up to .../code-generation
    """
    return Path(__file__).resolve().parents[4]


def _extract_sqlite_file_path(db_connection_txt: str) -> Optional[str]:
    """
    Extract the sqlite file path from the db_connection.txt contents.

    Supports lines like:
      - "Connection string: sqlite:////abs/path/to/file.db"
      - "File path: /abs/path/to/file.db"
    """
    for raw_line in db_connection_txt.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.lower().startswith("file path:"):
            value = line.split(":", 1)[1].strip()
            if value:
                return value

        if line.lower().startswith("connection string:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith("sqlite:////"):
                return value.replace("sqlite:////", "/", 1)

    return None


# PUBLIC_INTERFACE
def get_sqlite_config() -> SqliteConfig:
    """Load the SQLite configuration by reading the database container db_connection.txt."""
    repo_root = _repo_root_from_this_file()

    # The database container lives in a sibling workspace folder:
    # simple-notes-app-195720-195731/database/db_connection.txt
    db_conn_file = repo_root / "simple-notes-app-195720-195731" / "database" / "db_connection.txt"

    try:
        contents = db_conn_file.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Unable to locate database connection file at: {db_conn_file}. "
            "Ensure the database container workspace is present."
        ) from e

    db_path = _extract_sqlite_file_path(contents)
    if not db_path:
        raise RuntimeError(
            f"Could not parse SQLite DB file path from {db_conn_file}. "
            "Expected a 'File path:' or 'Connection string:' line."
        )

    # Validate path directory exists; the file itself should exist once init_db.py has run.
    db_dir = Path(db_path).expanduser().resolve().parent
    if not db_dir.exists():
        raise RuntimeError(f"SQLite database directory does not exist: {db_dir}")

    return SqliteConfig(db_path=str(Path(db_path).expanduser().resolve()))


# PUBLIC_INTERFACE
def get_connection() -> sqlite3.Connection:
    """Create a sqlite3 connection using the configured SQLite DB file path."""
    cfg = get_sqlite_config()

    # Use Row for dict-like access.
    conn = sqlite3.connect(cfg.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

