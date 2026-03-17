from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask(__name__)

DATABASE = "attendance.db"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            timeout=30,
            isolation_level=None
        )
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------- INIT DATABASE ----------------
def init_db():
    db = get_db()
    cur = db.cursor()

    # 🔥 IMPORTANT SETTINGS (NO LOCK)
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA synchronous=NORMAL;")

    # Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
    roll INTEGER PRIMARY KEY,
    name TEXT,
    total INTEGER DEFAULT 0,
    present INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
    )
    """)

    # Default login
    try:
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)", ("admin","1234"))
    except:
        pass

    db.commit()

# ---------------- ROUTES ----------------

@app.route('/')
def login_page():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    db = get_db()
    cur = db.cursor()

    user = request.form['username']
    pwd = request.form['password']

    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
    result = cur.fetchone()

    if result:
        return redirect(url_for('dashboard'))
    else:
        return "Invalid Login ❌"

@app.route('/dashboard')
def dashboard():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM students")
    data = cur.fetchall()

    return render_template("dashboard.html", students=data)

# ---------------- ADD STUDENT ----------------
@app.route('/add', methods=['POST'])
def add():
    db = get_db()
    cur = db.cursor()

    roll = request.form['roll']
    name = request.form['name']

    try:
        # Get current max total classes
        cur.execute("SELECT MAX(total) FROM students")
        max_total = cur.fetchone()[0]

        if max_total is None:
            max_total = 0

        # Insert student with same total
        cur.execute(
            "INSERT INTO students (roll,name,total,present) VALUES (?,?,?,?)",
            (roll, name, max_total, 0)
        )

        db.commit()
    except:
        pass

    return redirect(url_for('dashboard'))

# ---------------- SUBMIT ATTENDANCE ----------------
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    db = get_db()
    cur = db.cursor()

    data = request.form

    cur.execute("SELECT roll FROM students")
    students = cur.fetchall()

    # Increase total class for all
    cur.execute("UPDATE students SET total = total + 1")

    # Update present count
    for s in students:
        roll = str(s[0])
        status = data.get(roll)

        if status == "Present":
            cur.execute(
                "UPDATE students SET present = present + 1 WHERE roll=?",
                (roll,)
            )

    db.commit()
    return redirect(url_for('dashboard'))

# ---------------- RUN ----------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)