from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-to-something-random"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def db():
    return sqlite3.connect("diary.db")

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        time TEXT,
        day TEXT,
        mood TEXT,
        okay TEXT,
        trigger TEXT,
        thought TEXT,
        feeling TEXT,
        signal TEXT,
        source TEXT,
        loop TEXT,
        redirect TEXT,
        lesson TEXT,
        visibility TEXT
    )
""")

def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            time TEXT,
            day TEXT,
            mood TEXT,
            okay TEXT,
            trigger TEXT,
            thought TEXT,
            feeling TEXT,
            signal TEXT,
            source TEXT,
            loop TEXT,
            redirect TEXT,
            lesson TEXT,
            visibility TEXT
        )
    """)

    try:
        c.execute("ALTER TABLE entries ADD COLUMN image TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

@login_manager.user_loader
def load_user(user_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return User(row[0], row[1], row[2])
    return None

@app.route("/")
def home():
    return redirect(url_for("entries")) if current_user.is_authenticated else redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = db()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            error = "Username already exists."

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[2], password):
            login_user(User(row[0], row[1], row[2]))
            return redirect(url_for("entries"))

        error = "Wrong username or password."

    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():
    if request.method == "POST":
        conn = db()
        c = conn.cursor()

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename != "":
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
            image_file.save(image_path)

        c.execute("""
            INSERT INTO entries (
                user_id, time, day, mood, okay, trigger, thought, feeling,
                signal, source, loop, redirect, lesson, visibility, image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user.id,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            request.form["day"],
            request.form["mood"],
            request.form["okay"],
            request.form["trigger"],
            request.form["thought"],
            request.form["feeling"],
            request.form["signal"],
            request.form["source"],
            request.form["loop"],
            request.form["redirect"],
            request.form["lesson"],
            request.form["visibility"],
            image_filename
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("entries"))

    return render_template("new.html")

@app.route("/entries")
@login_required
def entries():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE user_id = ? ORDER BY id DESC", (current_user.id,))
    entries = c.fetchall()
    conn.close()
    return render_template("entries.html", entries=entries)

@app.route("/public")
def public_entries():
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT entries.*, users.username 
        FROM entries 
        JOIN users ON entries.user_id = users.id
        WHERE visibility = 'public'
        ORDER BY entries.id DESC
    """)
    entries = c.fetchall()
    conn.close()
    return render_template("public.html", entries=entries)

@app.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    conn = db()
    c = conn.cursor()

    c.execute(
        "DELETE FROM entries WHERE id = ? AND user_id = ?",
        (entry_id, current_user.id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("entries"))

@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM entries WHERE id = ? AND user_id = ?", (entry_id, current_user.id))
    entry = c.fetchone()

    if not entry:
        conn.close()
        return redirect(url_for("entries"))

    if request.method == "POST":
        c.execute("""
            UPDATE entries
            SET day = ?, mood = ?, okay = ?, trigger = ?, thought = ?, feeling = ?,
                signal = ?, source = ?, loop = ?, redirect = ?, lesson = ?, visibility = ?
            WHERE id = ? AND user_id = ?
        """, (
            request.form["day"],
            request.form["mood"],
            request.form["okay"],
            request.form["trigger"],
            request.form["thought"],
            request.form["feeling"],
            request.form["signal"],
            request.form["source"],
            request.form["loop"],
            request.form["redirect"],
            request.form["lesson"],
            request.form["visibility"],
            entry_id,
            current_user.id
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("entries"))

    conn.close()
    return render_template("edit.html", entry=entry)


@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM entries WHERE user_id = ?", (current_user.id,))
    total_entries = c.fetchone()[0]

    c.execute("""
        SELECT ROUND(AVG(CAST(mood AS INTEGER)), 1)
        FROM entries 
        WHERE user_id = ? AND mood != ''
    """, (current_user.id,))
    average_mood = c.fetchone()[0]

    c.execute("""
        SELECT trigger, COUNT(*) as count
        FROM entries
        WHERE user_id = ? AND trigger != ''
        GROUP BY trigger
        ORDER BY count DESC
        LIMIT 1
    """, (current_user.id,))
    common_trigger = c.fetchone()

    c.execute("""
        SELECT visibility, COUNT(*)
        FROM entries
        WHERE user_id = ?
        GROUP BY visibility
    """, (current_user.id,))
    visibility_stats = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_entries=total_entries,
        average_mood=average_mood,
        common_trigger=common_trigger,
        visibility_stats=visibility_stats
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
