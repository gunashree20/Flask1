
import os
import sqlite3
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify, g
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "mevi-workshop-development-key"
)

# Database configuration
os.makedirs(app.instance_path, exist_ok=True)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(app.instance_path, "management.db")
)


# ----------------------------------
# DATABASE CONNECTION
# ----------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


# ----------------------------------
# CREATE DATABASE TABLE
# ----------------------------------

def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                course TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_db()


# ----------------------------------
# DASHBOARD - GET
# ----------------------------------

@app.route("/")
def dashboard():

    db = get_db()

    total_students = db.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_courses = db.execute(
        "SELECT COUNT(DISTINCT course) FROM students"
    ).fetchone()[0]

    recent_students = db.execute(
        "SELECT * FROM students ORDER BY id DESC LIMIT 5"
    ).fetchall()

    return render_template(
        "index.html",
        total_students=total_students,
        total_courses=total_courses,
        recent_students=recent_students
    )


# ----------------------------------
# READ ALL STUDENTS - GET
# ----------------------------------

@app.route("/students", methods=["GET"])
def students():

    db = get_db()

    all_students = db.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    return render_template(
        "students.html",
        students=all_students
    )


# ----------------------------------
# CREATE STUDENT - POST (HTML FORM)
# ----------------------------------

@app.route("/students/add", methods=["POST"])
def add_student():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    course = request.form.get("course", "").strip()

    if not name or not email or not course:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("students"))

    if "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("students"))

    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO students (name, email, course)
            VALUES (?, ?, ?)
            """,
            (name, email, course)
        )

        db.commit()

        flash("Student added successfully!", "success")

    except sqlite3.IntegrityError:
        flash("This email address is already registered.", "error")

    return redirect(url_for("students"))


# ----------------------------------
# EDIT PAGE - GET (HTML)
# ----------------------------------

@app.route("/students/<int:student_id>/edit", methods=["GET"])
def edit_student(student_id):

    db = get_db()

    student = db.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("students"))

    return render_template(
        "edit_student.html",
        student=student
    )


# ----------------------------------
# UPDATE STUDENT - POST (HTML FORM)
# ----------------------------------

@app.route("/students/<int:student_id>/update", methods=["POST"])
def update_student_form(student_id):

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    course = request.form.get("course", "").strip()

    if not name or not email or not course or "@" not in email:
        flash("Please enter valid student details.", "error")
        return redirect(
            url_for("edit_student", student_id=student_id)
        )

    db = get_db()

    try:
        cursor = db.execute(
            """
            UPDATE students
            SET name = ?, email = ?, course = ?
            WHERE id = ?
            """,
            (name, email, course, student_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            flash("Student not found.", "error")
        else:
            flash("Student updated successfully!", "success")

    except sqlite3.IntegrityError:
        flash("This email address is already registered.", "error")

    return redirect(url_for("students"))


# ----------------------------------
# DELETE STUDENT - POST (HTML FORM)
# ----------------------------------

@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student_form(student_id):

    db = get_db()

    cursor = db.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    db.commit()

    if cursor.rowcount == 0:
        flash("Student not found.", "error")
    else:
        flash("Student record deleted.", "success")

    return redirect(url_for("students"))


# ==================================
# REST API - CRUD OPERATIONS
# ==================================


# ----------------------------------
# READ ALL STUDENTS - GET
# ----------------------------------

@app.route("/api/students", methods=["GET"])
def students_api():

    db = get_db()

    records = db.execute(
        """
        SELECT id, name, email, course
        FROM students
        ORDER BY id DESC
        """
    ).fetchall()

    return jsonify([
        dict(record) for record in records
    ]), 200


# ----------------------------------
# READ ONE STUDENT - GET
# ----------------------------------

@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):

    db = get_db()

    student = db.execute(
        "SELECT id, name, email, course FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student)), 200


# ----------------------------------
# CREATE STUDENT - POST
# ----------------------------------

@app.route("/api/students", methods=["POST"])
def create_student_api():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please send JSON data"
        }), 400

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    course = str(data.get("course") or "").strip()

    if not name or not email or not course:
        return jsonify({
            "error": "Name, email and course are required"
        }), 400

    if "@" not in email:
        return jsonify({
            "error": "Invalid email address"
        }), 400

    db = get_db()

    try:
        cursor = db.execute(
            """
            INSERT INTO students (name, email, course)
            VALUES (?, ?, ?)
            """,
            (name, email, course)
        )

        db.commit()

        return jsonify({
            "message": "Student added successfully",
            "student_id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Email already registered"
        }), 409


# ----------------------------------
# UPDATE STUDENT - PUT
# ----------------------------------

@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student_api(student_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please send JSON data"
        }), 400

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    course = str(data.get("course") or "").strip()

    if not name or not email or not course:
        return jsonify({
            "error": "Name, email and course are required"
        }), 400

    if "@" not in email:
        return jsonify({
            "error": "Invalid email address"
        }), 400

    db = get_db()

    try:
        cursor = db.execute(
            """
            UPDATE students
            SET name = ?, email = ?, course = ?
            WHERE id = ?
            """,
            (name, email, course, student_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify({
            "message": "Student updated successfully"
        }), 200

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Email already registered"
        }), 409


# ----------------------------------
# DELETE STUDENT - DELETE
# ----------------------------------

@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student_api(student_id):

    db = get_db()

    cursor = db.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    db.commit()

    if cursor.rowcount == 0:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify({
        "message": "Student deleted successfully"
    }), 200


# ----------------------------------
# HEALTH CHECK
# ----------------------------------

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy",
        "application": "MEVI Management Portal"
    })


# ----------------------------------
# RUN APPLICATION
# ----------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "5002"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
