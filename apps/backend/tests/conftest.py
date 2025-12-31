import pytest
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from alembic import command
from alembic.config import Config

# Get the backend directory path (where alembic.ini is located)
BACKEND_DIR = Path(__file__).parent.parent.resolve()
TEST_DB_PATH = BACKEND_DIR / ".pytest_db.sqlite"

# Set test environment variables BEFORE importing app
# Use absolute path for test database
os.environ["ENV"] = "testing"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.absolute()}"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["SESSION_SECRET"] = "test-secret-key-for-testing-only"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:3000"
os.environ["SESSION_IDLE_MINUTES"] = "5"
os.environ["SESSION_ABSOLUTE_MINUTES"] = "30"

# Now import app after env vars are set
from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.models import *  # Import all models to ensure they're registered

# Create test database engine using absolute path
# Use absolute path for SQLite to avoid path issues
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH.absolute()}"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def run_alembic_migrations():
    """Run Alembic migrations to head"""
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    # Override the database URL in alembic config
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    # script_location in alembic.ini is already set to "alembic" (relative to alembic.ini)
    # So we don't need to override it
    
    # Run migrations to head
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test with migrations applied"""
    # Dispose of any existing connections first (Windows SQLite locking issue)
    test_engine.dispose(close=True)
    import time
    time.sleep(0.2)  # Wait for file handles to release
    
    # Remove existing test DB if it exists
    # On Windows, we need to ensure no connections are open
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            # If file is still locked, wait a bit more and try again
            time.sleep(0.3)
            test_engine.dispose(close=True)
            try:
                TEST_DB_PATH.unlink()
            except PermissionError:
                # Last resort: just continue - migrations will handle it
                pass
    
    # Run Alembic migrations to create tables
    run_alembic_migrations()
    
    # Create session
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        # Dispose of all connections to release file locks (Windows)
        test_engine.dispose(close=True)
        # Clean up test DB file
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except PermissionError:
                # On Windows, sometimes the file is still locked briefly
                # This is okay - it will be cleaned up on next test run
                pass


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_admin_user(db: Session):
    """Create an admin user in the test database"""
    from app.models.admin_user import AdminUser
    from app.core.security import hash_password
    
    # Check if admin already exists
    admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if admin:
        return admin
    
    # Create admin user
    admin = AdminUser(
        username="admin",
        password_hash=hash_password("admin123")
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
