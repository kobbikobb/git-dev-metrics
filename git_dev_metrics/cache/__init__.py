"""SQLite cache for sealed PR/review data."""

from .cache import Cache, default_db_path

__all__ = [
    "Cache",
    "default_db_path",
]
