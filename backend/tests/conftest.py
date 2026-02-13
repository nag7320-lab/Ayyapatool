"""Pytest fixtures for Aypa TaxAI tests."""

import pytest

from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def db(app):
    """Create database tables."""
    _db.create_all()
    yield _db
    _db.drop_all()


@pytest.fixture(scope="function")
def session(db):
    """Create a new database session for each test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)
    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Get auth headers with a test user JWT."""
    # Register test user
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
    })

    # Login
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
    })

    token = response.get_json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
