from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from functools import wraps
from datetime import date, timedelta
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize DB
with app.app_context():
    init_db()
    seed_db()


def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # POST - handle registration
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Validation
    if not name or not email or not password:
        return render_template("register.html", error="All fields are required"), 400

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters"), 400

    # Hash password (using werkzeug)
    password_hash = generate_password_hash(password)

    # Check if email exists and create user
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return render_template("register.html", error="Email already registered"), 400

        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()

        # Start session
        session["user_id"] = user_id
        session["user_name"] = name

        return redirect(url_for("profile"))

    except sqlite3.IntegrityError:
        return render_template("register.html", error="Email already registered"), 400
    finally:
        conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST - handle login
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Email and password are required"), 400

    # Verify password (using werkzeug)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html", error="Invalid email or password"), 401


# ------------------------------------------------------------------ #
# Protected routes — require login                                    #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Get all expenses with category info
    cursor.execute("""
        SELECT e.id, e.amount, e.description, e.date, e.created_at,
               c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.date DESC, e.created_at DESC
    """, (user_id,))
    expenses = cursor.fetchall()

    # Get categories for dropdown
    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name")
    categories = cursor.fetchall()

    conn.close()

    # Calculate summaries
    total_spending = sum(e["amount"] for e in expenses)

    # Spending by category
    category_totals = {}
    for e in expenses:
        cat = e["category_name"]
        if cat not in category_totals:
            category_totals[cat] = {"total": 0, "icon": e["category_icon"], "color": e["category_color"]}
        category_totals[cat]["total"] += e["amount"]

    # Spending by month (last 6 months)
    today = date.today()
    month_totals = {}
    for i in range(6):
        month_start = date(today.year, today.month, 1) - timedelta(days=32 * i)
        month_start = month_start.replace(day=1)
        month_key = month_start.strftime("%Y-%m")
        month_name = month_start.strftime("%b %Y")
        month_totals[month_key] = {"name": month_name, "total": 0}

    for e in expenses:
        exp_date = e["date"]
        if isinstance(exp_date, str):
            exp_date = date.fromisoformat(exp_date)
        month_key = exp_date.strftime("%Y-%m")
        if month_key in month_totals:
            month_totals[month_key]["total"] += e["amount"]

    # Recent expenses (last 10)
    recent_expenses = expenses[:10]

    return render_template("profile.html",
                           user_name=session["user_name"],
                           total_spending=total_spending,
                           category_totals=category_totals,
                           month_totals=month_totals,
                           recent_expenses=recent_expenses,
                           categories=categories)


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Get categories for dropdown
    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name")
    categories = cursor.fetchall()

    if request.method == "GET":
        conn.close()
        return render_template("add_expense.html", categories=categories)

    # POST - handle expense creation
    category_id = request.form.get("category_id", type=int)
    amount = request.form.get("amount", type=float)
    description = request.form.get("description", "").strip()
    date_str = request.form.get("date", "")

    # Validation
    errors = []
    if not category_id:
        errors.append("Category is required")
    if not amount or amount <= 0:
        errors.append("Amount must be greater than 0")
    if not date_str:
        errors.append("Date is required")

    if errors:
        conn.close()
        return render_template("add_expense.html", categories=categories, errors=errors,
                               form_data=request.form), 400

    try:
        cursor.execute(
            "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, category_id, amount, description, date_str)
        )
        conn.commit()
        flash("Expense added successfully!", "success")
    except Exception as e:
        flash(f"Error adding expense: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Get categories for dropdown
    cursor.execute("SELECT id, name, icon, color FROM categories ORDER BY name")
    categories = cursor.fetchall()

    # Get expense (verify ownership)
    cursor.execute("""
        SELECT e.*, c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ? AND e.user_id = ?
    """, (id, user_id))
    expense = cursor.fetchone()

    if not expense:
        conn.close()
        flash("Expense not found", "error")
        return redirect(url_for("profile"))

    if request.method == "GET":
        conn.close()
        return render_template("edit_expense.html", expense=expense, categories=categories)

    # POST - handle expense update
    category_id = request.form.get("category_id", type=int)
    amount = request.form.get("amount", type=float)
    description = request.form.get("description", "").strip()
    date_str = request.form.get("date", "")

    # Validation
    errors = []
    if not category_id:
        errors.append("Category is required")
    if not amount or amount <= 0:
        errors.append("Amount must be greater than 0")
    if not date_str:
        errors.append("Date is required")

    if errors:
        conn.close()
        return render_template("edit_expense.html", expense=expense, categories=categories,
                               errors=errors, form_data=request.form), 400

    try:
        cursor.execute(
            "UPDATE expenses SET category_id = ?, amount = ?, description = ?, date = ? WHERE id = ? AND user_id = ?",
            (category_id, amount, description, date_str, id, user_id)
        )
        conn.commit()
        flash("Expense updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating expense: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense(id):
    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted:
        flash("Expense deleted successfully!", "success")
    else:
        flash("Expense not found", "error")

    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
