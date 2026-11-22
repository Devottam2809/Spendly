import pytest
from app import app
from database.db import init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DATABASE"] = ":memory:" # Or a temporary test database

    with app.test_client() as client:
        with app.app_context():
            init_db() # Seed with test data
        yield client

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
