"""
Teacher Attendance Management System
Console-based Python project using SQLite.
Run: python attendance_system.py
"""

import sqlite3
from datetime import date, datetime

DB_NAME = "attendance.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def setup_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
                UNIQUE(roll_no, attendance_date),
                FOREIGN KEY (roll_no) REFERENCES students(roll_no)
            )
        """)


def read_date(prompt="Enter date (YYYY-MM-DD), or press Enter for today: "):
    value = input(prompt).strip()
    if not value:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        print("Invalid date. Please use YYYY-MM-DD.")
        return None


def add_student():
    print("\n--- Add Student ---")
    roll_no = input("Roll number: ").strip()
    name = input("Student name: ").strip()
    class_name = input("Class/Division: ").strip()

    if not roll_no or not name or not class_name:
        print("All fields are required.")
        return

    try:
        with connect_db() as conn:
            conn.execute(
                "INSERT INTO students (roll_no, name, class_name) VALUES (?, ?, ?)",
                (roll_no, name, class_name),
            )
        print("Student added successfully.")
    except sqlite3.IntegrityError:
        print("A student with that roll number already exists.")


def view_students():
    print("\n--- Student List ---")
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT roll_no, name, class_name FROM students ORDER BY roll_no"
        ).fetchall()

    if not rows:
        print("No students found. Add students first.")
        return

    print(f"{'Roll No.':<14} {'Name':<28} {'Class/Division':<18}")
    print("-" * 62)
    for roll_no, name, class_name in rows:
        print(f"{roll_no:<14} {name:<28} {class_name:<18}")


def mark_attendance():
    print("\n--- Mark Attendance ---")
    attendance_date = read_date()
    if attendance_date is None:
        return

    with connect_db() as conn:
        students = conn.execute(
            "SELECT roll_no, name FROM students ORDER BY roll_no"
        ).fetchall()

    if not students:
        print("No students found. Add students first.")
        return

    print(f"Attendance date: {attendance_date}")
    print("Enter P for Present, A for Absent, or S to skip a student.")
    for roll_no, name in students:
        while True:
            status_input = input(f"{roll_no} - {name}: ").strip().upper()
            if status_input in ("P", "A", "S"):
                break
            print("Invalid choice. Enter P, A, or S.")

        if status_input == "S":
            continue

        status = "Present" if status_input == "P" else "Absent"
        with connect_db() as conn:
            conn.execute("""
                INSERT INTO attendance (roll_no, attendance_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT(roll_no, attendance_date)
                DO UPDATE SET status = excluded.status
            """, (roll_no, attendance_date, status))

    print("Attendance saved. Existing entries for this date were updated.")


def view_attendance():
    print("\n--- View Attendance by Date ---")
    attendance_date = read_date()
    if attendance_date is None:
        return

    with connect_db() as conn:
        rows = conn.execute("""
            SELECT s.roll_no, s.name, s.class_name, a.status
            FROM students s
            LEFT JOIN attendance a
              ON s.roll_no = a.roll_no AND a.attendance_date = ?
            ORDER BY s.roll_no
        """, (attendance_date,)).fetchall()

    if not rows:
        print("No students found.")
        return

    print(f"\nAttendance for {attendance_date}")
    print(f"{'Roll No.':<12} {'Name':<25} {'Class':<14} {'Status':<12}")
    print("-" * 65)
    for roll_no, name, class_name, status in rows:
        print(f"{roll_no:<12} {name:<25} {class_name:<14} {status or 'Not Marked':<12}")


def search_student():
    print("\n--- Search Student ---")
    roll_no = input("Enter roll number: ").strip()
    with connect_db() as conn:
        student = conn.execute("""
            SELECT roll_no, name, class_name
            FROM students WHERE roll_no = ?
        """, (roll_no,)).fetchone()

    if not student:
        print("Student not found.")
        return

    print(f"Roll number: {student[0]}")
    print(f"Name: {student[1]}")
    print(f"Class/Division: {student[2]}")


def attendance_report():
    print("\n--- Attendance Percentage Report ---")
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT s.roll_no, s.name,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                   COUNT(a.id) AS marked_count
            FROM students s
            LEFT JOIN attendance a ON s.roll_no = a.roll_no
            GROUP BY s.roll_no, s.name
            ORDER BY s.roll_no
        """).fetchall()

    if not rows:
        print("No students found.")
        return

    print(f"{'Roll No.':<12} {'Name':<25} {'Present':<10} {'Marked':<10} {'Percentage':<12}")
    print("-" * 72)
    for roll_no, name, present_count, marked_count in rows:
        percentage = (present_count / marked_count * 100) if marked_count else 0.0
        print(
            f"{roll_no:<12} {name:<25} {present_count:<10} "
            f"{marked_count:<10} {percentage:>7.2f}%"
        )
    print("\nPercentage is based only on dates when attendance was marked.")


def main():
    setup_database()
    while True:
        print("""
========================================
 TEACHER ATTENDANCE MANAGEMENT SYSTEM
========================================
1. Add student
2. View all students
3. Mark/update attendance
4. View attendance for a date
5. Search student by roll number
6. Attendance percentage report
0. Exit
""")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            view_students()
        elif choice == "3":
            mark_attendance()
        elif choice == "4":
            view_attendance()
        elif choice == "5":
            search_student()
        elif choice == "6":
            attendance_report()
        elif choice == "0":
            print("Thank you for using the Attendance Management System.")
            break
        else:
            print("Invalid option. Please choose from the menu.")


if __name__ == "__main__":
    main()
