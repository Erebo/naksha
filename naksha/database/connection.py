"""Database Engine, Session, and Configuration for NAKSHA."""
import os
from typing import Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from naksha.core.config import settings

# Read DATABASE_URL from settings (NAKSHA_DATABASE_URL)
DATABASE_URL = settings.database_url

# Dynamic engine cache keyed by URL
_engines = {}

def get_engine(url: Optional[str] = None):
    target_url = url or settings.database_url
    if target_url not in _engines:
        connect_args = {}
        if target_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engines[target_url] = create_engine(
            target_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False,
        )
    return _engines[target_url]

def get_session(url: Optional[str] = None) -> Session:
    eng = get_engine(url)
    maker = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return maker()

engine = get_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for obtaining a database session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
