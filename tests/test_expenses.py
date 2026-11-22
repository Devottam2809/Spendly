import pytest
import tempfile
import os
from app import app
from database.db import init_db, seed_db, get_db

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
        # Log in the user to perform CRUD (use client to maintain session)
        client.post('/login', data={
            'email': 'nitish@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_add_expense(client):
    rv = client.post('/expenses/add', data={
        'category_id': 1,
        'amount': 500.00,
        'description': 'Test expense',
        'date': '2026-11-22'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Expense added successfully!' in rv.data

def test_edit_expense(client):
    # Add one first
    rv = client.post('/expenses/add', data={
        'category_id': 1,
        'amount': 100.00,
        'description': 'To be edited',
        'date': '2026-11-22'
    }, follow_redirects=True)

    # Get the ID of the newly added expense from the database
    import sqlite3
    from database.db import get_db
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = 'nitish@example.com') ORDER BY id DESC LIMIT 1")
        expense = cursor.fetchone()
        conn.close()
        expense_id = expense['id']

    # Edit the expense
    rv = client.post(f'/expenses/{expense_id}/edit', data={
        'category_id': 2,
        'amount': 150.00,
        'description': 'Edited',
        'date': '2026-11-22'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Expense updated successfully!' in rv.data

def test_delete_expense(client):
    # Add one
    rv = client.post('/expenses/add', data={
        'category_id': 1,
        'amount': 50.00,
        'description': 'To be deleted',
        'date': '2026-11-22'
    }, follow_redirects=True)

    # Get the ID of the newly added expense from the database
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM expenses WHERE user_id = (SELECT id FROM users WHERE email = 'nitish@example.com') ORDER BY id DESC LIMIT 1")
        expense = cursor.fetchone()
        conn.close()
        expense_id = expense['id']

    rv = client.post(f'/expenses/{expense_id}/delete', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Expense deleted successfully!' in rv.data
