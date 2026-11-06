
import sqlite3
import pandas as pd

DATABASE_NAME = "students.db"


# 1. Create Database
def create_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            attendance REAL NOT NULL,
            study_hours REAL NOT NULL,
            mathematics REAL NOT NULL,
            science REAL NOT NULL,
            english REAL NOT NULL,
            computer_science REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# 2. Add Student
def add_student(student_id, attendance, study_hours,
                mathematics, science, english, computer_science):

    conn = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO students
            (student_id, attendance, study_hours,
             mathematics, science, english, computer_science)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id, attendance, study_hours,
            mathematics, science, english, computer_science
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


# 3. Get All Students
def get_students():
    conn = sqlite3.connect(DATABASE_NAME)

    try:
        df = pd.read_sql_query(
            "SELECT * FROM students ORDER BY id DESC",
            conn
        )
        return df

    finally:
        conn.close()


# 4. Update Student
def update_student(student_id, attendance, study_hours,
                   mathematics, science, english, computer_science):

    conn = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE students
            SET attendance = ?,
                study_hours = ?,
                mathematics = ?,
                science = ?,
                english = ?,
                computer_science = ?
            WHERE student_id = ?
        """, (
            attendance, study_hours,
            mathematics, science, english, computer_science,
            student_id
        ))

        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


# 5. Delete Student
def delete_student(student_id):
    conn = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM students WHERE student_id = ?",
            (student_id,)
        )

        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


# 6. Run Database
if __name__ == "__main__":
    create_database()
    print("Database ready!")
    print("All database functions are ready!")
