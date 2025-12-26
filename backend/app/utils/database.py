import sqlite3
from pathlib import Path
from typing import Any, Iterable

from app.config import Settings

DatabaseConnection: sqlite3.Connection | None = None


def GetConnection() -> sqlite3.Connection:
    global DatabaseConnection
    if DatabaseConnection is None:
        DatabasePath = Path(Settings.DatabaseFile).expanduser().resolve()
        DatabasePath.parent.mkdir(parents=True, exist_ok=True)
        DatabaseConnection = sqlite3.connect(
            DatabasePath,
            check_same_thread=False
        )
        DatabaseConnection.row_factory = sqlite3.Row
        DatabaseConnection.execute("PRAGMA foreign_keys = ON;")
    return DatabaseConnection


def ExecuteScript(SqlText: str) -> None:
    Connection = GetConnection()
    Connection.executescript(SqlText)
    Connection.commit()


def ExecuteQuery(SqlText: str, Parameters: Iterable[Any] | None = None) -> None:
    Connection = GetConnection()
    Connection.execute(SqlText, Parameters or [])
    Connection.commit()


def FetchAll(SqlText: str, Parameters: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    Connection = GetConnection()
    Cursor = Connection.execute(SqlText, Parameters or [])
    Rows = Cursor.fetchall()
    return [dict(Row) for Row in Rows]


def FetchOne(SqlText: str, Parameters: Iterable[Any] | None = None) -> dict[str, Any] | None:
    Connection = GetConnection()
    Cursor = Connection.execute(SqlText, Parameters or [])
    Row = Cursor.fetchone()
    if Row is None:
        return None
    return dict(Row)
