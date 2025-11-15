"""Pytest fixtures and configuration for test suite"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
import os
import tempfile


@pytest.fixture(scope="function")
def db_session():
    """
    Create an in-memory SQLite database for testing

    Yields:
        SQLAlchemy Session for test database

    Cleanup:
        Drops all tables after test completes
    """
    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def temp_db_file():
    """
    Create a temporary SQLite database file for integration tests

    Yields:
        Path to temporary database file

    Cleanup:
        Removes temporary file after test completes
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)
