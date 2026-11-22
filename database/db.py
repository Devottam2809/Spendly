import sqlite3
import os
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent / "expense_tracker.db"


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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT NOT NULL DEFAULT '📦',
            color TEXT NOT NULL DEFAULT '#1a472a'
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
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_category ON expenses(user_id, category_id)")

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

    # Default categories
    categories = [
        ("Food", "🍔", "#c17f24"),
        ("Transport", "🚌", "#5b7fa6"),
        ("Bills", "💡", "#8b5e83"),
        ("Health", "🏥", "#c0392b"),
        ("Shopping", "🛍️", "#e67e22"),
        ("Entertainment", "🎮", "#9b59b6"),
        ("Education", "📚", "#27ae60"),
        ("Other", "📦", "#1a472a"),
    ]

    for name, icon, color in categories:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name, icon, color) VALUES (?, ?, ?)",
            (name, icon, color)
        )

    # Sample user (password: "password123")
    import hashlib
    password_hash = hashlib.sha256("password123".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Nitish Kumar", "nitish@example.com", password_hash)
    )
    user_id = cursor.lastrowid

    # Sample expenses
    from datetime import date, timedelta
    today = date.today()

    sample_expenses = [
        (user_id, 1, 250.00, "Lunch with colleagues", today - timedelta(days=1)),
        (user_id, 2, 45.00, "Bus fare", today - timedelta(days=1)),
        (user_id, 3, 1200.00, "Electricity bill", today - timedelta(days=5)),
        (user_id, 4, 800.00, "Pharmacy", today - timedelta(days=7)),
        (user_id, 1, 180.00, "Coffee and snacks", today - timedelta(days=10)),
        (user_id, 5, 3500.00, "New headphones", today - timedelta(days=14)),
        (user_id, 6, 500.00, "Movie tickets", today - timedelta(days=18)),
        (user_id, 2, 60.00, "Metro card top-up", today - timedelta(days=20)),
        (user_id, 1, 320.00, "Weekend dinner", today - timedelta(days=25)),
        (user_id, 3, 950.00, "Internet bill", today - timedelta(days=30)),
    ]

    for user_id, cat_id, amount, desc, exp_date in sample_expenses:
        cursor.execute(
            "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, cat_id, amount, desc, exp_date.isoformat())
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded!")