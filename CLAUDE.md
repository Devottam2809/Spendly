# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** - A personal finance tracker built with Flask. Users can register, log in, and track expenses with categories, view spending summaries, and manage their financial data.

## Architecture

```
├── app.py                 # Main Flask application with routes
├── database/
│   ├── __init__.py        # Package marker (empty)
│   └── db.py              # Database layer: get_db(), init_db(), seed_db()
├── static/
│   ├── css/style.css      # Complete styling (responsive, CSS variables)
│   └── js/main.js         # Client-side JS (currently empty)
├── templates/
│   ├── base.html          # Base template with navbar, footer
│   ├── landing.html       # Marketing landing page
│   ├── register.html      # Registration form
│   └── login.html         # Login form
├── requirements.txt       # Flask, Werkzeug, pytest, pytest-flask
└── expense_tracker.db     # SQLite database (gitignored)
```

### Database Schema

- **users**: id, name, email (unique), password_hash, created_at
- **categories**: id, name (unique), icon, color
- **expenses**: id, user_id (FK), category_id (FK), amount, description, date, created_at
- Indexes on expenses(user_id, date DESC) and expenses(user_id, category_id)

## Commands

### Setup
```bash
python -m venv venv
source venv/Scripts/activate   # Windows
pip install -r requirements.txt
python -m database.db          # Initialize & seed database
```

### Run Development Server
```bash
python app.py                  # Runs on http://127.0.0.1:5001
```

### Run Tests
```bash
pytest                         # All tests
pytest -v                      # Verbose
pytest tests/test_auth.py      # Single test file
pytest -k "test_login"         # Filter by name
```

## Current State (as of initial commit)

### Implemented
- Landing page with hero, features, CTA
- Register & login pages (templates only, no backend logic)
- Database schema with users, categories, expenses tables
- Sample data seeding (1 user, 8 categories, 10 expenses)
- Responsive CSS with CSS variables, DM Serif Display + DM Sans fonts

### Placeholder Routes in app.py (need implementation)
- `POST /register` - Create account, hash password, start session
- `POST /login` - Verify credentials, start session
- `GET /logout` - Clear session
- `GET /profile` - User dashboard with spending summaries
- `GET/POST /expenses/add` - Add expense form & handler
- `GET/POST /expenses/<id>/edit` - Edit expense
- `GET /expenses/<id>/delete` - Delete expense

### Test User (from seed_db)
- Email: `nitish@example.com`
- Password: `password123`

## Development Notes

- Uses SQLite with `row_factory=sqlite3.Row` for dict-like row access
- Foreign keys enabled via `PRAGMA foreign_keys = ON`
- Passwords hashed with SHA-256 (upgrade to bcrypt/argon2 recommended for production)
- Templates use Jinja2 with `base.html` as parent
- Static files served from `/static/`
- Port 5001 (non-standard to avoid conflicts)

## Next Steps Priority

1. **Authentication**: Implement register/login/logout with Flask sessions
2. **Expense CRUD**: Add list, create, edit, delete routes + templates
3. **Profile/Dashboard**: Spending summaries by category/time period
4. **Tests**: Add pytest-flask tests for auth and expense routes