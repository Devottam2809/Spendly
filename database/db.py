import sqlite3
import os
from pathlib import Path
from werkzeug.security import generate_password_hash


def get_db():
    """Return a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
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

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded!")



def seed_db():
    """Insert sample data for development."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Sample user (password: "demo123")
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )
    user_id = cursor.lastrowid

    # Sample expenses
    from datetime import date, timedelta
    today = date.today()

    sample_expenses = [
        (user_id, 250.00, "Food", (today - timedelta(days=1)).isoformat(), "Lunch with colleagues"),
        (user_id, 45.00, "Transport", (today - timedelta(days=2)).isoformat(), "Bus fare"),
        (user_id, 1200.00, "Bills", (today - timedelta(days=5)).isoformat(), "Electricity bill"),
        (user_id, 800.00, "Health", (today - timedelta(days=7)).isoformat(), "Pharmacy"),
        (user_id, 180.00, "Food", (today - timedelta(days=10)).isoformat(), "Coffee and snacks"),
        (user_id, 3500.00, "Shopping", (today - timedelta(days=14)).isoformat(), "New headphones"),
        (user_id, 500.00, "Entertainment", (today - timedelta(days=18)).isoformat(), "Movie tickets"),
        (user_id, 60.00, "Other", (today - timedelta(days=20)).isoformat(), "Metro card top-up"),
    ]

    for user_id, amount, category, exp_date, desc in sample_expenses:
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, exp_date, desc)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded!")

