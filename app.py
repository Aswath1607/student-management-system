from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"


# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            course TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cursor.execute("SELECT * FROM users")
    if not cursor.fetchall():
        cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                       ("admin", "admin123", "admin"))
        cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                       ("staff", "staff123", "staff"))

    conn.commit()
    conn.close()


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[0]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= STUDENTS PAGE =================

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    return render_template("index.html",
                           students=students,
                           role=session["role"])


# ================= ADD STUDENT =================

@app.route("/add", methods=["POST"])
def add_student():
    if "user" not in session:
        return redirect("/login")

    name = request.form["name"]
    age = request.form["age"]
    course = request.form["course"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name,age,course) VALUES (?,?,?)",
                   (name, age, course))
    conn.commit()
    conn.close()

    return redirect("/?added=1")


# ================= DELETE =================

@app.route("/delete/<int:id>")
def delete_student(id):
    if "user" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/?deleted=1")


# ================= EDIT =================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        cursor.execute("""
            UPDATE students
            SET name=?, age=?, course=?
            WHERE id=?
        """, (name, age, course, id))

        conn.commit()
        conn.close()

        return redirect("/?updated=1")

    cursor.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cursor.fetchone()
    conn.close()

    return render_template("edit.html", student=student)


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT course, COUNT(*) FROM students GROUP BY course")
    data = cursor.fetchall()

    labels = [row[0] for row in data]
    counts = [row[1] for row in data]

    conn.close()

    return render_template("dashboard.html",
                           total_students=total_students,
                           labels=labels,
                           counts=counts,
                           role=session["role"])


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)