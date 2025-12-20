# db.py
import sqlite3
from datetime import datetime

DB_PATH = "omr_results.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    إنشاء جداول قاعدة البيانات (results + students) إذا لم تكن موجودة.
    """
    conn = get_connection()
    cur = conn.cursor()

    # جدول نتائج التصحيح
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        student_name TEXT,
        exam_code TEXT,
        score REAL,
        answers TEXT,
        created_at TEXT
    )
    """)

    # جدول الطلاب
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        student_name TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- نتائج التصحيح ----------------

def save_result(student_id, student_name, exam_code, score, answers_list):
    """
    حفظ نتيجة في جدول النتائج.
    """
    conn = get_connection()
    cur = conn.cursor()

    answers_str = ",".join(str(a) for a in answers_list)
    now = datetime.now().isoformat(timespec="seconds")

    cur.execute("""
        INSERT INTO results (student_id, student_name, exam_code, score, answers, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, student_name, exam_code, score, answers_str, now))

    conn.commit()
    conn.close()


def fetch_results(exam_code=None):
    """
    جلب نتائج الطلاب (الكل أو حسب كود الامتحان).
    يرجع: (id, student_id, student_name, exam_code, score, answers, created_at)
    """
    conn = get_connection()
    cur = conn.cursor()

    if exam_code:
        cur.execute("""
            SELECT id, student_id, student_name, exam_code, score, answers, created_at
            FROM results
            WHERE exam_code = ?
            ORDER BY created_at DESC
        """, (exam_code,))
    else:
        cur.execute("""
            SELECT id, student_id, student_name, exam_code, score, answers, created_at
            FROM results
            ORDER BY created_at DESC
        """)

    rows = cur.fetchall()
    conn.close()
    return rows


def clear_all_results():
    """
    حذف جميع الصفوف من جدول النتائج فقط (results).
    لا يحذف جدول الطلاب.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM results")
    conn.commit()
    conn.close()


# ---------------- الطلاب (CRUD) ----------------

def fetch_students():
    """
    جلب جميع الطلاب.
    يرجع: (id, student_id, student_name, created_at)
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, student_id, student_name, created_at
        FROM students
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def add_student(student_id, student_name):
    """
    إضافة طالب جديد.
    student_id يجب أن يكون فريدًا.
    """
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    try:
        cur.execute("""
            INSERT INTO students (student_id, student_name, created_at)
            VALUES (?, ?, ?)
        """, (student_id, student_name, now))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Student ID already exists.")
    conn.close()


def update_student(db_id, student_id, student_name):
    """
    تعديل بيانات طالب.
    db_id هو الـ id في جدول students.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE students
            SET student_id = ?, student_name = ?
            WHERE id = ?
        """, (student_id, student_name, db_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Student ID already exists.")
    conn.close()


def delete_student(db_id):
    """
    حذف طالب حسب الـ id في جدول students.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()
