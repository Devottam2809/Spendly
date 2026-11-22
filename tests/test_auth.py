import pytest
import tempfile
import os
from app import app
from database.db import init_db, seed_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Use a temporary file database for testing (SQLite :memory: is per-connection)
    db_fd, db_path = tempfile.mkstemp()
    app.config["DATABASE"] = db_path

    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_landing(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Spendly' in rv.data

def test_register_login_logout(client):
    # Register
    rv = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data

    # Logout
    client.get('/logout')

    # Login
    rv = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data
