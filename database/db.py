import sqlite3
import os
from pathlib import Path
from werkzeug.security import generate_password_hash
from flask import current_app, has_app_context


DB_PATH = "expense_tracker.db"


def get_db():
    """Return a SQLite connection with row_factory and foreign keys enabled.

    Uses Flask app's DATABASE config if available (for testing with :memory:),
    otherwise defaults to the file-based database.
    """
    if has_app_context() and current_app.config.get("DATABASE"):
        db_path = current_app.config["DATABASE"]
    else:
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT NOT NULL,
            color TEXT NOT NULL
        )
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # Indexes for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expenses_user_date
        ON expenses(user_id, date DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expenses_user_category
        ON expenses(user_id, category_id)
    """)

    conn.commit()
    conn.close()


def seed_db():
    """Insert sample data for development."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed categories first (fixed list from spec)
    categories = [
        ("Food", "🍔", "#ef4444"),
        ("Transport", "🚌", "#3b82f6"),
        ("Bills", "📄", "#f59e0b"),
        ("Health", "💊", "#10b981"),
        ("Entertainment", "🎮", "#8b5cf6"),
        ("Shopping", "🛍️", "#ec4899"),
        ("Other", "📦", "#6b7280"),
    ]

    category_ids = {}
    for name, icon, color in categories:
        cursor.execute(
            "INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)",
            (name, icon, color)
        )
        category_ids[name] = cursor.lastrowid

    # Demo user (password: "demo123")
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )
    demo_user_id = cursor.lastrowid

    # Test user for pytest (password: "password123")
    password_hash_test = generate_password_hash("password123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Nitish", "nitish@example.com", password_hash_test)
    )
    test_user_id = cursor.lastrowid

    # Sample expenses for demo user
    from datetime import date, timedelta
    today = date.today()

    sample_expenses = [
        (demo_user_id, category_ids["Food"], 250.00, (today - timedelta(days=1)).isoformat(), "Lunch with colleagues"),
        (demo_user_id, category_ids["Transport"], 45.00, (today - timedelta(days=2)).isoformat(), "Bus fare"),
        (demo_user_id, category_ids["Bills"], 1200.00, (today - timedelta(days=5)).isoformat(), "Electricity bill"),
        (demo_user_id, category_ids["Health"], 800.00, (today - timedelta(days=7)).isoformat(), "Pharmacy"),
        (demo_user_id, category_ids["Food"], 180.00, (today - timedelta(days=10)).isoformat(), "Coffee and snacks"),
        (demo_user_id, category_ids["Shopping"], 3500.00, (today - timedelta(days=14)).isoformat(), "New headphones"),
        (demo_user_id, category_ids["Entertainment"], 500.00, (today - timedelta(days=18)).isoformat(), "Movie tickets"),
        (demo_user_id, category_ids["Other"], 60.00, (today - timedelta(days=20)).isoformat(), "Metro card top-up"),
    ]

    for user_id, cat_id, amount, exp_date, desc in sample_expenses:
        cursor.execute(
            "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, cat_id, amount, desc, exp_date)
        )

    # Sample expenses for test user (so tests have data to work with)
    test_expenses = [
        (test_user_id, category_ids["Food"], 100.00, today.isoformat(), "Test expense 1"),
        (test_user_id, category_ids["Transport"], 50.00, today.isoformat(), "Test expense 2"),
    ]

    for user_id, cat_id, amount, exp_date, desc in test_expenses:
        cursor.execute(
            "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, cat_id, amount, desc, exp_date)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded!")