import pytest
import sqlite3
from yt_dlp_bot.database import _setup_tables

@pytest.fixture
def db_conn():
    """Provides an in-memory SQLite connection with the schema initialized."""
    con = sqlite3.connect(":memory:")
    _setup_tables(con)
    return con
