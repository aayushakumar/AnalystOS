from app.config import Settings, settings
from app.db.connection import DuckDBManager, db_manager


def get_db() -> DuckDBManager:
    return db_manager


def get_settings() -> Settings:
    return settings
