import pytest
from app import app
from database.db import init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DATABASE"] = ":memory:"

    with app.test_client() as client:
        with app.app_context():
            init_db()
            # Log in the user to perform CRUD
            client.post('/login', data={
                'email': 'nitish@example.com',
                'password': 'password123'
            }, follow_redirects=True)
        yield client

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
    client.post('/expenses/add', data={
        'category_id': 1,
        'amount': 100.00,
        'description': 'To be edited',
        'date': '2026-11-22'
    })

    # Edit (assuming it gets ID 11 based on initial seed data)
    rv = client.post('/expenses/11/edit', data={
        'category_id': 2,
        'amount': 150.00,
        'description': 'Edited',
        'date': '2026-11-22'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Expense updated successfully!' in rv.data

def test_delete_expense(client):
    # Add one
    client.post('/expenses/add', data={
        'category_id': 1,
        'amount': 50.00,
        'description': 'To be deleted',
        'date': '2026-11-22'
    })

    rv = client.post('/expenses/12/delete', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Expense deleted successfully!' in rv.data
